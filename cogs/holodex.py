# coding=utf-8
import discord
from discord import (
    ui,
    Interaction,
    Embed,
    Option,
    SelectOption,
    ButtonStyle,
    InputTextStyle,
)
from discord.ext import commands
import os
import zoneinfo
from pathlib import Path
from dotenv import load_dotenv
import time
import json
from math import ceil

import holodex_api
import logger
from json_assistant import ClipsRecord
import youtube_download
import youtube_api
from thumbnail_generator import ThumbnailGenerator
from cogs.general import Basics, Events, MUSIC_CMD_CHANNELS


error_color = 0xF1411C
default_color = 0x5FE1EA
now_tz = zoneinfo.ZoneInfo("Asia/Taipei")
base_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = str(Path(__file__).parent.parent.absolute())

load_dotenv(dotenv_path=os.path.join(base_dir, "TOKEN.env"))
holodex_client = holodex_api.HolodexClient(str(os.getenv("HOLODEX_TOKEN")))


class Holodex(commands.Cog):
    def __init__(self, bot: commands.Bot, real_logger: logger.CreateLogger):
        self.bot = bot
        self.real_logger = real_logger

    @staticmethod
    def slice_section_list(section_list: list, page_no: int) -> tuple[tuple, list]:
        if len(section_list) <= 25:
            return (1, 1), section_list
        split_section_list = []
        split_count = ceil(len(section_list) / 25)
        for i in range(split_count):
            split_section_list.append(
                section_list[i * 25 : min((i + 1) * 25, len(section_list))]
            )
        selected_page_no = min(page_no, split_count + 1)
        selected_page = split_section_list[selected_page_no - 1]
        return (selected_page_no, split_count), selected_page

    def section_selection(
        self,
        author: discord.Member | discord.User,
        video_instance: youtube_download.Video,
        bit_rate: int,
        sections_list: list,
        add_to_musicbot_queue: bool = False,
        upload_to_youtube: bool = False,
    ) -> ui.View:
        view = ui.View(disable_on_timeout=True)
        # generate sections
        selections = []
        for sect in sections_list:
            raw_label = sect["name"]
            if len(raw_label) > 100:
                raw_label = raw_label[:97] + "..."
            raw_original_artist = sect["original_artist"]
            if len(raw_original_artist) > 90:
                raw_original_artist = raw_original_artist[:87] + "..."
            selections.append(
                SelectOption(
                    label=raw_label,
                    value=str(sections_list.index(sect)),
                    description=f"By {raw_original_artist}，{sect['end'] - sect['start']} 秒",
                )
            )
        menu = ui.Select(
            placeholder="選取要下載的片段",
            min_values=1,
            max_values=1,
            options=selections,
        )

        async def callback(interaction: Interaction):
            await interaction.response.defer()
            if interaction.user.id == author.id:
                section_pos = int(menu.values[0])
                section = sections_list[section_pos]
                start_time = time.time()
                embed = Embed(
                    title="片段已確認",
                    description=f"已開始下載所選取的片段。",
                    color=default_color,
                )
                embed.add_field(
                    name="來源影片",
                    value=f"[{video_instance.get_title()}]({video_instance.url})",
                    inline=False,
                )
                embed.add_field(
                    name="片段歌曲",
                    value=f"**{section['name']}** - by *{section['original_artist']}*",
                    inline=False,
                )
                embed.add_field(
                    name="片段時間軸",
                    value="`%02d:%02d:%02d` - `%02d:%02d:%02d` (`%d` 秒)"
                    % (
                        section["start"] // 3600,
                        (section["start"] % 3600) // 60,
                        section["start"] % 60,
                        section["end"] // 3600,
                        (section["end"] % 3600) // 60,
                        section["end"] % 60,
                        sect["end"] - sect["start"],
                    ),
                    inline=False,
                )
                if section["art"] is not None:
                    embed.set_thumbnail(url=section["art"])
                if upload_to_youtube:
                    await interaction.edit_original_response(embed=embed, view=None)
                    file_name = f"{video_instance.get_id()}_{section['id'][-12:]}.mp4"
                    existed_id = ClipsRecord().get_youtube_id(file_name)
                    if existed_id is None:
                        file_path = os.path.join(
                            parent_dir,
                            "ytdl",
                            file_name,
                        )
                        await Basics.run_blocking(
                            self.bot,
                            video_instance.download_section_in_mp4,
                            file_path,
                            section["start"],
                            section["end"],
                        )
                        end_time = time.time()
                        time_delta = end_time - start_time
                        await interaction.edit_original_response(
                            content=f"下載共花了 `{round(time_delta, 3)}` 秒 "
                            f"(`{round((section['end'] - section['start'])/time_delta, 3)}` x)",
                            embed=embed,
                            view=None,
                        )
                        clip_title = (
                            f"【{video_instance.full_info['channel']}】{section['name']} / {section['original_artist']}"
                            "【純剪輯】"
                        )
                        clip_description = f"""
原直播：{video_instance.url}

此剪輯片段由Allen Bot產生，使用Holodex API取得時間軸資料。
本功能仍在測試中，且可能隨時下線並不另行通知。
Holodex API：https://docs.holodex.net/
"""
                        yt_uploader = youtube_api.YouTubeUploader(
                            file_path=file_path,
                            title=clip_title,
                            description=clip_description,
                        )
                        try:
                            yt_uploader.setup_credentials()
                            video_info = await Basics.run_blocking(
                                self.bot,
                                yt_uploader.upload,
                            )
                            ClipsRecord().add_clip(
                                file_name=file_name, youtube_id=video_info["id"]
                            )
                            embed = Embed(
                                title="上傳完成！",
                                description=f"片段 **{section['name']}** 已經上傳至YouTube！",
                                color=default_color,
                            )
                            embed.add_field(
                                name="連結",
                                value="https://youtu.be/" + video_info["id"],
                                inline=False,
                            )
                            embed.add_field(
                                name="影片無法觀看？",
                                value="影片在剛上傳時，YouTube需要將其進一步處理才會發布。請稍待幾分鐘再回來。",
                                inline=False,
                            )
                        except KeyError:
                            embed = Embed(
                                title="錯誤：沒有Refresh Token",
                                description="尚未有Refresh Token儲存在機器人內，因此無法上傳YouTube。\n"
                                "請使用`/holodex update_token`更新Refresh Token。",
                                color=error_color,
                            )
                        except Exception as e:
                            if "Refresh token has expired or invalid." in str(e):
                                embed = Embed(
                                    title="錯誤：Refresh Token無效",
                                    description="機器人所儲存的Refresh Token似乎已過期或失效。\n"
                                    "請使用`/holodex update_token`更新Refresh Token。",
                                    color=error_color,
                                )
                            else:
                                embed = Embed(
                                    title="錯誤", description="發生未知錯誤。", color=error_color
                                )
                                embed.add_field(
                                    name="錯誤訊息", value=f"```{e}```", inline=False
                                )
                                embed.add_field(
                                    name="Debug: Clip Title",
                                    value="```" + clip_title + "```",
                                    inline=False,
                                )
                                embed.add_field(
                                    name="Debug: Clip Description",
                                    value="```" + clip_description + "```",
                                    inline=False,
                                )
                    else:
                        embed = Embed(
                            title="此片段已在YouTube上！",
                            description=f"片段 **{section['name']}** 已可在YouTube上觀看！",
                            color=default_color,
                        )
                        embed.add_field(
                            name="連結",
                            value="https://youtu.be/" + existed_id,
                            inline=False,
                        )
                    await interaction.edit_original_response(embed=embed)
                else:
                    embed.add_field(
                        name="預估下載時間(依片段長度粗估)",
                        value="約 `%d`~`%d` 秒"
                        % (
                            (section["end"] - section["start"]) / 1.9,
                            (section["end"] - section["start"]) / 1.2,
                        ),
                        inline=False,
                    )
                    embed.set_footer(text="請注意，下載時間可能會比/musicdl還要久。請在數分鐘後回來查看。")
                    await interaction.edit_original_response(embed=embed, view=None)

                    if not add_to_musicbot_queue:
                        metadata = {
                            "title": section["name"],
                            "artist": holodex_client.get_video_channel(
                                video_instance.get_id()
                            ),
                            "thumbnail_url": video_instance.get_thumbnail(),
                        }
                    else:
                        metadata = {}
                    file_name = (
                        f"{video_instance.get_id()}_{section['id'][-12:]}_{bit_rate}"
                    )
                    result = await Basics.run_blocking(
                        self.bot,
                        Basics.ConfirmDownload.youtube_start_download,
                        video_instance,
                        metadata,
                        bit_rate,
                        file_name,
                        [section["start"], section["end"]],
                    )
                    end_time = time.time()
                    time_delta = end_time - start_time
                    message = await interaction.edit_original_response(
                        content=f"下載共花了 `{round(time_delta, 3)}` 秒 "
                        f"(`{round((section['end'] - section['start'])/time_delta, 3)}` x)",
                        file=result,
                    )
                    if add_to_musicbot_queue:
                        file_url = message.attachments[0].url
                        check_vc_result = await Events.check_voice_channel(
                            self, interaction.guild
                        )
                        if isinstance(check_vc_result, str):
                            embed = discord.Embed(
                                title="錯誤",
                                description="機器人自動加入語音頻道時失敗。",
                                color=error_color,
                            )
                            embed.add_field(name="錯誤訊息", value=check_vc_result)
                            await interaction.followup.send(embed=embed)
                        elif isinstance(check_vc_result, discord.VoiceChannel):
                            if interaction.user in check_vc_result.members:
                                await interaction.channel.send(
                                    "ap!p " + file_url, delete_after=0.5
                                )
                            else:
                                embed = Embed(
                                    title="錯誤：使用者不在語音頻道內",
                                    description="你必須在Allen Music Bot的語音頻道內，才可使用此功能。",
                                    color=error_color,
                                )
                                await interaction.followup.send(embed=embed)
            else:
                embed = Embed(
                    title="錯誤：非指令使用者",
                    description=f"你不是指令的使用者。僅有<@{author.id}>可使用此選單。",
                    color=error_color,
                )
                await interaction.followup.send(embed=embed, ephemeral=True)

        menu.callback = callback
        view.add_item(menu)

        return view

    class ThumbnailGeneratorWindow(ui.Modal):
        def __init__(self, song_name: str, channel_name: str, video_path: str):
            super().__init__(title="設定縮圖文字")
            self.add_item(
                ui.InputText(
                    style=InputTextStyle.short,
                    label="主要標題 (圖片正下方)",
                    value=song_name,
                    required=True,
                )
            )
            self.add_item(
                ui.InputText(
                    style=InputTextStyle.short,
                    label="小標題 (圖片左上方)",
                    value=channel_name.replace("Channel", ""),
                    required=False,
                )
            )
            self.add_item(
                ui.InputText(
                    style=InputTextStyle.short,
                    label="色碼 (HEX)",
                    value="#FFFFFF",
                    min_length=7,
                    max_length=7,
                    required=True,
                )
            )
            self.video_path = video_path

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            title = self.children[0].value
            subtitle = self.children[1].value
            color = self.children[2].value
            thumb_gen = ThumbnailGenerator(video_source_path=self.video_path)
            thumb_gen.extract_random_frames(10)
            thumb_gen.load_images_to_canvases()
            thumb_gen.write_title(title, color)
            thumb_gen.write_subtitle(subtitle, color)
            output_images = thumb_gen.save_canvases()
            await interaction.edit_original_response(
                content="Output test",
                files=[discord.File(i) for i in output_images],
            )

    class ThumbnailGeneratorButton(ui.View):
        def __init__(
            self,
            author: discord.User | discord.Member,
            song_name: str,
            channel_name: str,
            video_path: str,
        ):
            super().__init__(disable_on_timeout=True)
            self.author = author
            self.song_name = song_name
            self.channel_name = channel_name
            self.video_path = video_path

        @discord.ui.button(label="製作縮圖", style=ButtonStyle.blurple)
        async def start_thumb_gen(self, button, interaction: discord.Interaction):
            if interaction.user.id == self.author.id:
                await interaction.response.send_modal(
                    Holodex.ThumbnailGeneratorWindow(
                        self.song_name, self.channel_name, self.video_path
                    )
                )
            else:
                embed = Embed(
                    title="錯誤：非指令使用者",
                    description=f"你不是指令的使用者。僅有<@{self.author.id}>可使用此選單。",
                    color=error_color,
                )
                await interaction.followup.send(embed=embed, ephemeral=True)

    class TokenSubmissionWindow(ui.Modal):
        def __init__(self):
            super().__init__(title="提交Refresh Token")
            self.add_item(
                ui.InputText(
                    style=InputTextStyle.long,
                    label="Refresh Token",
                    placeholder="貼上剪貼簿中的Refresh Token",
                    required=True,
                )
            )

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            token = self.children[0].value
            if youtube_api.YouTubeUploader.refresh_token_is_valid(token):
                with open(
                    os.path.join(parent_dir, "google_client_secret.json"),
                    "r",
                    encoding="utf-8",
                ) as f:
                    data = json.load(f)
                    data["refresh_token"] = token
                with open(
                    os.path.join(parent_dir, "google_client_secret.json"),
                    "w",
                    encoding="utf-8",
                ) as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                embed = Embed(
                    title="已儲存Refresh Token",
                    description="此Refresh Token有效。已儲存新的Refresh Token。",
                    color=default_color,
                )
            else:
                embed = Embed(
                    title="錯誤：Refresh Token無效",
                    description="你所提供的Refresh Token經檢查無效。",
                    color=error_color,
                )
            embed.add_field(
                name="Refresh Token", value="||" + token + "||", inline=False
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            await interaction.edit_original_response(view=None)

    class TokenSubmissionButtons(ui.View):
        def __init__(self, author: discord.User | discord.Member):
            super().__init__(timeout=120, disable_on_timeout=True)
            self.author = author
            url_btn = ui.Button(
                style=ButtonStyle.url,
                label="點此取得新Refresh Token",
                url="https://accounts.google.com/o/oauth2/v2/auth/oauthchooseaccount?scope=https%3A%2F%2Fwww.googleapis"
                ".com%2Fauth%2Fyoutube.upload&response_type=token&redirect_uri=https%3A%2F%2Falllen95wei.github.io%2F"
                "&client_id=301053688733-0oighbmuqurd094jd9ttlb8ouoa4vjrp.apps.googleusercontent.com&service=lso&o2v"
                "=2&ddm=0&flowName=GeneralOAuthFlow",
            )
            self.add_item(url_btn)

        @ui.button(style=ButtonStyle.green, label="提交Refresh Token")
        async def submit_callback(self, button, interaction: discord.Interaction):
            if interaction.user.id == self.author.id:
                await interaction.response.send_modal(Holodex.TokenSubmissionWindow())
            else:
                embed = Embed(
                    title="錯誤：非指令使用者",
                    description=f"你不是指令的使用者。僅有<@{self.author.id}>可使用此選單。",
                    color=error_color,
                )
                await interaction.followup.send(embed=embed, ephemeral=True)

    HOLODEX_CMDS = discord.SlashCommandGroup(name="holodex")

    @HOLODEX_CMDS.command(name="download", description="從Holodex取得直播時間軸，並下載特定片段")
    async def holodex_download(
        self,
        ctx,
        url: Option(str, name="直播連結", description="欲抓取時間軸的直播連結(僅限YouTube)"),
        page: Option(
            int,
            name="頁數",
            description="若時間軸的片段數量超過25個，則會自動分頁",
            min_value=1,
            required=False,
        ) = 1,
        bitrate: Option(
            int,
            name="位元率",
            description="下載後，轉換為MP3時所使用的位元率，會影響檔案的大小與品質",
            choices=[96, 128, 160],
            required=False,
        ) = 128,
        add_to_musicbot_queue: Option(
            bool,
            name="加入音樂機器人佇列",
            description="下載後，是否自動新增至Allen Music Bot佇列中",
            required=False,
        ) = False,
    ):
        await ctx.defer()
        view = ui.View()
        if add_to_musicbot_queue and ctx.channel.id not in MUSIC_CMD_CHANNELS:
            embed = Embed(
                title="錯誤：需在音樂機器人指令頻道使用",
                description="你啟用了「加入音樂機器人佇列」功能。此功能需在音樂機器人指令頻道使用。",
                colour=error_color,
            )
        else:
            try:
                video = youtube_download.Video(url)
                section_list = holodex_client.fetch_video_timeline(video.get_id())
                if "youtube" not in video.get_extractor():
                    embed = Embed(
                        title="錯誤：連結不是YouTube連結",
                        description="你所提供的連結不是YouTube的連結。請提供有效的YouTube連結。",
                        color=error_color,
                    )
                    embed.add_field(
                        name="Debug: Extractor",
                        value=f"```{video.get_extractor()}```",
                        inline=False,
                    )
                elif len(section_list) == 0:
                    embed = Embed(
                        title="錯誤：沒有片段",
                        description="此影片在Holodex中沒有標記任何片段。",
                        color=error_color,
                    )
                    embed.add_field(
                        name="想下載整部影片嗎？",
                        value="請使用</musicdl:1195621958218420245>",
                        inline=False,
                    )
                    embed.add_field(
                        name="來源影片", value=f"[{video.get_title()}]({url})", inline=False
                    )
                    embed.set_image(url=video.get_thumbnail())
                else:
                    embed = Embed(
                        title="選擇片段",
                        description="請從下拉式選單選擇要下載的片段。",
                        color=default_color,
                    )
                    embed.add_field(
                        name="來源影片", value=f"[{video.get_title()}]({url})", inline=False
                    )
                    embed.add_field(
                        name="片段數量", value=f"`{len(section_list)}`個", inline=False
                    )
                    embed.set_image(url=video.get_thumbnail())
                    if len(section_list) > 25:
                        selected_page_no, selected_page = self.slice_section_list(
                            section_list, page
                        )
                        embed.add_field(
                            name="頁數",
                            value=f"第 {selected_page_no[0]} / {selected_page_no[1]} 頁",
                            inline=False,
                        )
                    else:
                        selected_page = section_list
                    view = self.section_selection(
                        ctx.author,
                        video,
                        bitrate if not add_to_musicbot_queue else 128,
                        selected_page,
                        add_to_musicbot_queue,
                    )
            except Exception as e:
                embed = Embed(
                    title="錯誤",
                    description="發生未知錯誤。",
                    color=error_color,
                )
                embed.add_field(name="錯誤訊息", value=f"```{str(e)}```", inline=False)
        await ctx.respond(embed=embed, view=view)

    @commands.is_owner()
    @HOLODEX_CMDS.command(
        name="clip_and_upload", description="(開發者限定)從Holodex取得直播時間軸、下載特定片段後上傳YouTube"
    )
    async def holodex_clip(
        self,
        ctx,
        url: Option(str, name="直播連結", description="欲抓取時間軸的直播連結(僅限YouTube)"),
        keyword: Option(
            str,
            name="關鍵字",
            description="搜尋曲名或原唱名稱包含關鍵字的片段",
            max_length=20,
            required=False,
        ) = None,
        page: Option(
            int,
            name="頁數",
            description="若時間軸的片段數量超過25個，則會自動分頁",
            min_value=1,
            required=False,
        ) = 1,
    ):
        await ctx.defer()
        view = ui.View()
        try:
            video = youtube_download.Video(url)
            section_list = holodex_client.fetch_video_timeline(video.get_id())
            if "youtube" not in video.get_extractor():
                embed = Embed(
                    title="錯誤：連結不是YouTube連結",
                    description="你所提供的連結不是YouTube的連結。請提供有效的YouTube連結。",
                    color=error_color,
                )
                embed.add_field(
                    name="Debug: Extractor",
                    value=f"```{video.get_extractor()}```",
                    inline=False,
                )
            elif len(section_list) == 0:
                embed = Embed(
                    title="錯誤：沒有片段",
                    description="此影片在Holodex中沒有標記任何片段。",
                    color=error_color,
                )
                embed.add_field(
                    name="來源影片", value=f"[{video.get_title()}]({url})", inline=False
                )
                embed.set_image(url=video.get_thumbnail())
            else:
                embed = Embed(
                    title="選擇片段",
                    description="請從下拉式選單選擇要下載的片段。",
                    color=default_color,
                )
                embed.add_field(
                    name="來源影片", value=f"[{video.get_title()}]({url})", inline=False
                )
                embed.add_field(
                    name="片段數量", value=f"`{len(section_list)}`個", inline=False
                )
                embed.set_image(url=video.get_thumbnail())
                if keyword is not None:
                    search_result = []
                    for s in section_list:
                        if keyword in s["name"] or keyword in s["original_artist"]:
                            search_result.append(s)
                    if len(search_result) == 0:
                        embed.add_field(
                            name="⚠️沒有符合關鍵字的片段",
                            value=f"此影片的時間軸中，沒有任何符合關鍵字 `{keyword}` 的片段。\n目前回傳未經搜尋的結果。",
                            inline=False,
                        )
                    else:
                        section_list = search_result
                        embed.add_field(
                            name="已套用搜尋",
                            value=f"目前僅列出符合關鍵字 `{keyword}` 的片段。",
                            inline=False,
                        )
                selected_page_no, selected_page = self.slice_section_list(
                    section_list, page
                )
                embed.add_field(
                    name="頁數",
                    value=f"第 {selected_page_no[0]} / {selected_page_no[1]} 頁",
                    inline=False,
                )
                view = self.section_selection(
                    ctx.author,
                    video,
                    0,
                    selected_page,
                    False,
                    True,
                )
        except Exception as e:
            embed = Embed(
                title="錯誤",
                description="發生未知錯誤。",
                color=error_color,
            )
            embed.add_field(name="錯誤訊息", value=f"```{str(e)}```", inline=False)
        await ctx.respond(embed=embed, view=view)

    @commands.is_owner()
    @HOLODEX_CMDS.command(
        name="update_token", description="(開發者限定)更新上傳YouTube所用的Refresh Token"
    )
    async def holodex_update_token(self, ctx):
        embed = Embed(
            title="更新Refresh Token",
            description="請先取得新的Refresh Token後，再點擊「提交Refresh Token」按鈕。",
            color=default_color,
        )
        await ctx.respond(
            embed=embed, view=self.TokenSubmissionButtons(ctx.author), ephemeral=True
        )

    @commands.is_owner()
    @HOLODEX_CMDS.command(name="test", description="測試")
    async def holodex_test(self, ctx):
        await ctx.respond(view=self.ThumbnailGeneratorButton(ctx.author, "Test", "test", "test.mp4"))


def setup(bot):
    bot.add_cog(Holodex(bot, bot.logger))
    bot.logger.info(f'"{Holodex.__name__}"已被載入。')
