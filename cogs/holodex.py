# coding=utf-8
import discord
from discord import ui, Interaction, Embed, Option, SelectOption
from discord.ext import commands
import os
import zoneinfo
from pathlib import Path
from dotenv import load_dotenv
import time

import holodex_api
import logger
import youtube_download
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

    def section_selection(
        self,
        author: discord.Member | discord.User,
        video_instance: youtube_download.Video,
        bit_rate: int,
        sections_list: list,
        add_to_musicbot_queue: bool = False,
    ) -> ui.View:
        view = ui.View()
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
                embed.add_field(
                    name="預估下載時間(依片段長度粗估)",
                    value="約 `%d`~`%d` 秒"
                    % (
                        (sect["end"] - sect["start"]) / 1.9,
                        (sect["end"] - sect["start"]) / 1.2,
                    ),
                    inline=False,
                )
                if section["art"] is not None:
                    embed.set_thumbnail(url=section["art"])
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
                start_time = time.time()
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
                            f"(`{round((sect['end'] - sect['start'])/time_delta, 3)}` x)",
                    file=result,
                )
                if add_to_musicbot_queue:
                    file_url = message.attachments[0].url
                    check_vc_result = await Events.check_voice_channel(
                        self, interaction.guild
                    )
                    if isinstance(check_vc_result, str):
                        embed = discord.Embed(
                            title="錯誤", description="機器人自動加入語音頻道時失敗。", color=error_color
                        )
                        embed.add_field(name="錯誤訊息", value=check_vc_result)
                        await interaction.followup.send(embed=embed)
                    elif isinstance(check_vc_result, discord.VoiceChannel):
                        self.real_logger.debug(f"已連線至語音頻道：{check_vc_result.name}")
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

    HOLODEX_CMDS = discord.SlashCommandGroup(name="holodex")

    @HOLODEX_CMDS.command(name="download", description="從Holodex取得直播時間軸，並下載特定片段")
    async def holodex_download(
        self,
        ctx,
        url: Option(str, name="直播連結", description="欲抓取時間軸的直播連結(僅限YouTube)"),
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
                    view = self.section_selection(
                        ctx.author,
                        video,
                        bitrate if not add_to_musicbot_queue else 128,
                        section_list,
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


def setup(bot):
    bot.add_cog(Holodex(bot, bot.logger))
    bot.logger.info(f'"{Holodex.__name__}"已被載入。')
