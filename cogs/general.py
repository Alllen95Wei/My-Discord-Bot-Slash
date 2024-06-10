# coding=utf-8
import discord
from discord.ext import commands
from discord.ext import tasks
from discord import Option, Interaction
from discord.ui import Modal
from discord.ui import InputText
from discord import InputTextStyle
import os
import git
import time
import datetime
import zoneinfo
import functools
import urllib.parse
from typing import Callable
from random import choice
from random import randint
from pathlib import Path
from math import floor
from copy import deepcopy

import logger
import json_assistant
import detect_pc_status
from read_RPC import get_RPC_context
from youtube_to_mp3 import main_dl
import youtube_download as yt_download
from bullshit import bullshit

error_color = 0xF1411C
default_color = 0x5FE1EA
now_tz = zoneinfo.ZoneInfo("Asia/Taipei")
base_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = str(Path(__file__).parent.parent.absolute())

exp_reports_list = {}
exp_report_template = {
    "join_at": 0,
    "channels": [],
    "partners": [],
    "time_exp": 0,
    "activity_bonus": 0,
}


class Basics(commands.Cog):
    def __init__(self, bot: commands.Bot, real_logger: logger.CreateLogger):
        self.bot = bot
        self.real_logger = real_logger

    @staticmethod
    async def run_blocking(bot, blocking_func: Callable, *args, **kwargs):
        """Runs a blocking function in a non-blocking way"""
        func = functools.partial(blocking_func, *args, **kwargs)
        return await bot.loop.run_in_executor(None, func)

    # Modals, Views (UI)

    class GiftInTurn(discord.ui.View):
        def __init__(
            self,
            giver: discord.User | discord.Member,
            real_logger: logger.CreateLogger,
        ):
            super().__init__(timeout=3600 * 3)
            self.giver = giver
            self.real_logger = real_logger

        @discord.ui.button(
            label="回送10點作為感謝(不會扣除你的經驗值！)", style=discord.ButtonStyle.blurple, emoji="🎁"
        )
        async def gift_btn(
            self, button: discord.ui.Button, interaction: discord.Interaction
        ):
            button.disabled = True
            json_assistant.User(self.giver.id).add_exp("text", 10)
            self.real_logger.info(f"{self.giver.name}#{self.giver.discriminator} 獲得回禮。")
            embed = discord.Embed(
                title="🎁已送出回禮！",
                description=f"你已贈送{self.giver.mention}**10點文字經驗值**作為回禮！",
                color=default_color,
            )
            await interaction.response.edit_message(embed=embed, view=self)
            giver_embed = discord.Embed(
                title="🎁收到回禮！",
                description=f"{interaction.user.mention}送你**10點文字經驗值**作為回禮！",
                color=default_color,
            )
            try:
                await self.giver.send(embed=giver_embed)
            except discord.errors.Forbidden:
                self.real_logger.warning(
                    f"無法傳送回禮通知給 {self.giver.name}#{self.giver.discriminator}，因為該用戶已關閉私人訊息。"
                )

    class ConfirmDownload(discord.ui.View):
        def __init__(
            self,
            outer_instance,
            video_instance: yt_download.Video,
            metadata: dict,
            bit_rate: int = 128,
        ):
            super().__init__()
            self.outer_instance = outer_instance
            self.m_video = video_instance
            self.metadata = metadata
            self.bit_rate = bit_rate

        @discord.ui.button(style=discord.ButtonStyle.blurple, label="確認下載", emoji="✅")
        async def yes_btn(
            self, button: discord.ui.Button, interaction: discord.Interaction
        ):
            await interaction.response.defer()
            button.disabled = True
            if self.metadata == {}:
                embed = discord.Embed(
                    title="確認下載", description="已開始下載，請稍候。", color=default_color
                )
                embed.add_field(
                    name="影片名稱",
                    value=f"[{self.m_video.get_title()}]({self.m_video.url})",
                    inline=False,
                )
                embed.add_field(
                    name="影片長度", value=f"`{self.m_video.get_length()}`秒", inline=False
                )
                embed.set_image(url=self.m_video.get_thumbnail())
                embed.set_footer(text="下載所需時間依影片長度、網路狀況及影片來源端而定。")
                await interaction.edit_original_response(embed=embed, view=None)
                result = await Basics.run_blocking(
                    self.outer_instance.bot,
                    self.youtube_start_download,
                    self.m_video,
                    self.metadata,
                    self.bit_rate,
                )
                try:
                    await interaction.edit_original_response(file=result)
                except Exception as e:
                    if "Request entity too large" in str(e):
                        embed = discord.Embed(
                            title="錯誤", description="檔案過大，無法上傳。", color=error_color
                        )
                        embed.add_field(name="錯誤訊息", value=f"```{e}```", inline=False)
                    else:
                        embed = discord.Embed(
                            title="錯誤", description="發生未知錯誤。", color=error_color
                        )
                        embed.add_field(name="錯誤訊息", value=f"```{e}```", inline=False)
                    await interaction.edit_original_response(embed=embed)
            else:
                embed = discord.Embed(
                    title="編輯後設資料",
                    description="請點擊下方按鈕，以編輯、確認後設資料。",
                    color=default_color,
                )
                embed.add_field(
                    name="為何會出現這則訊息？",
                    value="由於你使用指令時，將`加入後設資料`設為`True`。\n"
                    "如要忽略此步驟，請將`加入後設資料`設為`False`。",
                )
                await interaction.edit_original_response(
                    embed=embed,
                    view=Basics.MP3MetadataEditorView(
                        self.outer_instance, self.m_video, self.bit_rate, self.metadata
                    ),
                )

        @discord.ui.button(style=discord.ButtonStyle.red, label="取消下載", emoji="❌")
        async def no_btn(
            self, button: discord.ui.Button, interaction: discord.Interaction
        ):
            button.disabled = True
            embed = discord.Embed(title="取消下載", description="已取消下載。", color=error_color)
            await interaction.response.edit_message(embed=embed, view=None)

        @staticmethod
        def youtube_start_download(
            video_instance: yt_download.Video, metadata: dict, bit_rate: int
        ) -> discord.File:
            if metadata != {}:
                file_name = video_instance.get_id() + "_" + str(bit_rate) + "_MD"
            else:
                file_name = video_instance.get_id() + "_" + str(bit_rate)
            mp3_file_name = f"{file_name}.mp3"
            mp3_file_path = os.path.join(parent_dir, "ytdl", mp3_file_name)
            if (metadata == {} and os.path.exists(mp3_file_path)) or main_dl(
                video_instance, file_name, mp3_file_path, metadata, bit_rate
            ) == "finished":
                return discord.File(mp3_file_path)

    class MP3MetadataEditor(Modal):
        def __init__(
            self,
            outer_instance,
            video: yt_download.Video,
            bit_rate: int,
            prefill_metadata: dict,
        ):
            super().__init__(title="後設資料編輯器")
            self.bot = outer_instance.bot
            self.real_logger = outer_instance.real_logger
            self.video = video
            self.bit_rate = bit_rate

            self.add_item(
                InputText(
                    style=InputTextStyle.short,
                    label="標題",
                    value=prefill_metadata["title"],
                    placeholder="將儲存於TIT2 (ID3v2)",
                )
            )
            self.add_item(
                InputText(
                    style=InputTextStyle.short,
                    label="作者",
                    value=prefill_metadata["artist"],
                    placeholder="將儲存於TPE1 (ID3v2)",
                )
            )
            self.add_item(
                InputText(
                    style=InputTextStyle.short,
                    label="縮圖連結",
                    value=prefill_metadata["thumbnail_url"],
                    placeholder="儲存為PNG編碼後，將儲存於APIC - Type 3 (ID3v2)",
                )
            )

        async def callback(self, interaction: Interaction):
            await interaction.response.defer()
            metadata = {
                "title": self.children[0].value if self.children[0].value else "",
                "artist": self.children[1].value if self.children[1].value else "",
                "thumbnail_url": self.children[2].value
                if self.children[2].value
                else "",
            }
            embed = discord.Embed(
                title="確認下載", description="已開始下載，請稍候。", color=default_color
            )
            embed.add_field(
                name="後設資料皆採用ID3v2.3標記。",
                value="[點此](https://zh.wikipedia.org/zh-tw/ID3)了解ID3標記",
                inline=False,
            )
            embed.add_field(name="標題 (後設資料)", value=metadata["title"], inline=False)
            embed.add_field(name="作者 (後設資料)", value=metadata["artist"], inline=False)
            embed.set_image(url=metadata["thumbnail_url"])
            await interaction.edit_original_response(embed=embed, view=None)
            try:
                result = await Basics.run_blocking(
                    self.bot,
                    Basics.ConfirmDownload.youtube_start_download,
                    self.video,
                    metadata,
                    self.bit_rate,
                )
                try:
                    await interaction.edit_original_response(file=result)
                except Exception as e:
                    if "Request entity too large" in str(e):
                        embed = discord.Embed(
                            title="錯誤", description="檔案過大，無法上傳。", color=error_color
                        )
                        embed.add_field(name="錯誤訊息", value=f"```{e}```", inline=False)
                    else:
                        embed = discord.Embed(
                            title="錯誤", description="發生未知錯誤。", color=error_color
                        )
                        embed.add_field(name="錯誤訊息", value=f"```{e}```", inline=False)
                    await interaction.edit_original_response(embed=embed)
            except Exception as e:
                embed = discord.Embed(
                    title="錯誤：下載失敗", description="下載影片時發生錯誤。", color=error_color
                )
                embed.add_field(name="錯誤訊息", value=f"```{e}```", inline=False)
                await interaction.edit_original_response(embed=embed)

    class MP3MetadataEditorView(discord.ui.View):
        def __init__(
            self,
            outer_instance,
            video: yt_download.Video,
            bit_rate: int,
            prefill_metadata: dict,
        ):
            super().__init__(timeout=300)

            self.outer_instance = outer_instance
            self.video = video
            self.bit_rate = bit_rate
            self.prefill_metadata = prefill_metadata

        @discord.ui.button(label="點此編輯後設資料", style=discord.ButtonStyle.green, emoji="📝")
        async def editor_btn(
            self, button: discord.ui.Button, interaction: discord.Interaction
        ):
            await interaction.response.send_modal(
                Basics.MP3MetadataEditor(
                    self.outer_instance,
                    self.video,
                    self.bit_rate,
                    self.prefill_metadata,
                )
            )

    # Slash Cmds

    @discord.slash_command(name="ping", description="查詢機器人PING值(ms)。")
    async def ping(
        self, ctx, 私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False  # noqa
    ):
        embed = discord.Embed(title="PONG!✨", color=default_color)
        embed.add_field(name="PING值", value=f"`{round(self.bot.latency * 1000)}` ms")
        await ctx.respond(embed=embed, ephemeral=私人訊息)

    @discord.slash_command(name="help", description="提供指令協助。")
    async def help_cmd(
        self, ctx, 私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False  # noqa
    ):
        embed = discord.Embed(title="指令協助", color=default_color)
        embed.add_field(
            name="想要知道如何使用本機器人？",
            value="請參閱在GitHub上的[Wiki]"
            "(https://github.com/Alllen95Wei/My-Discord-Bot-Slash/wiki/)。",
        )
        await ctx.respond(embed=embed, ephemeral=私人訊息)

    @discord.slash_command(name="about", description="提供關於這隻機器人的資訊。")
    async def about(
        self, ctx, 私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False  # noqa
    ):
        embed = discord.Embed(title="關於", color=default_color)
        embed.set_thumbnail(url=self.bot.user.display_avatar)
        embed.add_field(
            name="程式碼與授權",
            value="本機器人由<@657519721138094080>維護，使用[Py-cord]"
            "(https://github.com/Pycord-Development/pycord)進行開發。\n"
            "本機器人的程式碼及檔案皆可在[這裡]"
            "(https://github.com/Alllen95Wei/My-Discord-Bot-Slash)查看。",
            inline=True,
        )
        embed.add_field(
            name="聯絡", value="如果有任何技術問題及建議，請聯絡<@657519721138094080>。", inline=True
        )
        repo = git.Repo(search_parent_directories=True)
        update_msg = repo.head.reference.commit.message
        raw_sha = repo.head.object.hexsha
        sha = raw_sha[:7]
        embed.add_field(name=f"分支訊息：{sha}", value=update_msg, inline=False)
        year = time.strftime("%Y")
        embed.set_footer(text=f"©Allen Why, {year} | 版本：commit {sha[:7]}")
        await ctx.respond(embed=embed, ephemeral=私人訊息)

    @discord.slash_command(name="bugflag", description="機器人發生錯誤，或運作不如預期？使用此指令立即標記！")
    async def bugflag(self, ctx):
        self.real_logger.bugflag(f"{ctx.author} 標記了錯誤。")
        self.real_logger.bugflag(f"頻道ID：{ctx.channel.id} ({ctx.channel})")
        dev_embed = discord.Embed(
            title="bugflag",
            description=f"{ctx.author.mention} 標記了錯誤。",
            color=default_color,
        )
        dev_embed.add_field(name="時間", value=f"<t:{int(time.time())}:F>", inline=False)
        dev_embed.add_field(name="頻道", value=f"<#{ctx.channel.id}>", inline=False)
        dev_embed.add_field(
            name="對方的使用者資料 (RAW)",
            value=f"```{json_assistant.User(ctx.author.id).get_raw_info()}```",
            inline=False,
        )
        await self.bot.get_user(657519721138094080).send(embed=dev_embed)
        embed = discord.Embed(
            title="已標記！", description="機器人已標記了錯誤，同時通知開發者！", color=default_color
        )
        embed.add_field(
            name="你的使用者資料 (RAW)",
            value=f"```{json_assistant.User(ctx.author.id).get_raw_info()}```",
        )
        await ctx.respond(embed=embed)

    @discord.slash_command(name="dps", description="查詢伺服器電腦的CPU及記憶體使用率。")
    async def dps(
        self, ctx, 私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False  # noqa
    ):
        embed = discord.Embed(title="伺服器電腦資訊", color=default_color)
        embed.add_field(name="CPU使用率", value=f"{detect_pc_status.get_cpu_usage()}%")
        embed.add_field(
            name="記憶體使用率", value=f"{detect_pc_status.get_ram_usage_detail()}"
        )
        await ctx.respond(embed=embed, ephemeral=私人訊息)

    @discord.slash_command(name="ama", description="就是8號球，給你這個問題的隨機回答。")
    async def ama(
        self,
        ctx,
        問題: Option(str, "你要問的問題", required=True),  # noqa
        私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False,  # noqa
    ):
        ans1 = ("g", "s", "b")
        ans_g = (
            "看起來不錯喔",
            "肯定的",
            "我覺得可行",
            "絕對OK",
            "是的",
            "確定",
            "200 OK",
            "100 Continue",
            "Just do it",
        )
        ans_s = (
            "現在別問我",
            "404 Not Found",
            "你的問題超出宇宙的範圍了",
            "答案仍在變化",
            "400 Bad Request",
            "這問題實在沒人答得出來",
            "Answer=A=Ans=答案",
            "最好不要現在告訴你",
            "300 Multiple Choices",
            "去問瑪卡巴卡更快",
            "您撥的電話無人接聽，嘟聲後開始計費。",
            "對不起，您播的號碼是空號，請查明後再撥。",
        )

        ans_b = (
            "不可能",
            "否定的",
            "不值得",
            "等等等等",
            "No no no",
            "我拒絕",
            "我覺得不行耶",
            "403 Forbidden",
            "這樣不好",
        )

        ball_result1 = choice(ans1)
        if ball_result1 == "g":
            ball_result2 = choice(ans_g)
            ball_result1 = "🟢"
        elif ball_result1 == "s":
            ball_result2 = choice(ans_s)
            ball_result1 = "🟡"
        else:
            ball_result2 = choice(ans_b)
            ball_result1 = "🔴"
        embed = discord.Embed(
            title="8號球", description=f"你的問題：{問題}", color=default_color
        )
        embed.add_field(
            name="回答", value=f'{ball_result1}"{ball_result2}"', inline=False
        )
        await ctx.respond(embed=embed, ephemeral=私人訊息)

    @discord.slash_command(name="bullshit", description="唬爛。")
    # @commands.cooldown(1, 60, commands.BucketType.user)
    async def bullshit_cmd(
        self,
        ctx,
        關鍵字: Option(str, "想要唬爛的關鍵字", required=True),  # noqa: PEP 3131
        字數: Option(  # noqa
            int,
            "想要唬爛的字數(最多1000)",
            min_value=1,
            max_value=1000,
            required=False,
        ) = 200,
        顯著標示關鍵字: Option(bool, "是否顯著標示關鍵字", required=False) = True,  # noqa: PEP 3131
        私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False,  # noqa
    ):
        await ctx.defer(ephemeral=私人訊息)
        content = ""
        try:
            result = bullshit(關鍵字, 字數)
            embed = discord.Embed(
                title="唬爛", description="以下是唬爛的結果。", color=default_color
            )
            embed.add_field(name="關鍵字", value=關鍵字, inline=False)
            embed.add_field(name="指定字數", value=字數, inline=True)
            embed.add_field(name="實際字數", value=str(len(result)), inline=True)
            if len(result) > 1024:
                embed.add_field(name="內容", value="(字數過長，改使用一般訊息回覆)", inline=False)
                content = f"```{result}```"
            else:
                result = result.replace(關鍵字, f"`{關鍵字}`" if 顯著標示關鍵字 else 關鍵字)
                embed.add_field(name="內容", value=result, inline=False)
                embed.set_footer(text="以上內容皆由透過「唬爛產生器」API產生，與本機器人無關。")
        except Exception as e:
            embed = discord.Embed(
                title="錯誤", description=f"發生錯誤：`{e}`", color=error_color
            )
        await ctx.respond(embed=embed, content=content, ephemeral=私人訊息)

    @discord.slash_command(name="random", description="在指定數字範圍隨機取得一數。")
    async def random(
        self,
        ctx,
        range_min: Option(name="min", description="最小值", required=True, input_type=int),
        range_max: Option(name="max", description="最大值", required=True, input_type=int),
        私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False,  # noqa
    ):
        ans = randint(int(range_min), int(range_max))
        embed = discord.Embed(
            title="隨機", description=f"數字範圍：{range_min}~{range_max}", color=default_color
        )
        embed.add_field(name="結果", value=f"`{ans}`", inline=False)
        await ctx.respond(embed=embed, ephemeral=私人訊息)

    @discord.slash_command(name="qrcode", description="將輸入的文字轉為QR Code。")
    async def qrcode(
        self,
        ctx,
        內容: Option(str, "要轉換的文字", required=True),  # noqa
        私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False,  # noqa
    ):
        text = urllib.parse.quote(內容)
        url = f"https://quickchart.io/chart?cht=qr&chs=500x500&choe=UTF-8&chld=H|1&chl={text}"
        embed = discord.Embed(
            title="QR Code", description=f"內容：{內容}", color=default_color
        )
        embed.set_image(url=url)
        await ctx.respond(embed=embed, ephemeral=私人訊息)

    @discord.slash_command(name="daily", description="每日簽到！")
    async def daily(
        self,
        ctx,
        贈與使用者: Option(discord.User, "要贈與每日獎勵的對象", required=False) = None,  # noqa
        私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False,  # noqa
    ):
        last_claimed_time = json_assistant.User(
            ctx.author.id
        ).get_last_daily_reward_claimed()
        if last_claimed_time is None:
            last_claimed_time = 0.0
        last_claimed_time_str = datetime.datetime.fromtimestamp(
            last_claimed_time, tz=now_tz
        ).strftime("%Y-%m-%d")
        now_time_str = datetime.datetime.fromtimestamp(time.time(), tz=now_tz).strftime(
            "%Y-%m-%d"
        )
        if now_time_str == last_claimed_time_str:
            embed = discord.Embed(
                title="每日簽到",
                description=f"你今天已經在<t:{int(last_claimed_time)}:t>簽到過了！",
                color=error_color,
            )
        else:
            random_reference = randint(1, 200)
            if 贈與使用者 and 贈與使用者.id != ctx.author.id:  # 贈禮
                if 1 <= random_reference < 81:  # 40%
                    reward = 10
                elif 81 <= random_reference < 121:  # 20%
                    reward = 20
                elif 121 <= random_reference < 161:  # 20%
                    reward = 50
                else:  # 20%
                    reward = 100
                # if 1 <= random_reference < 91:  # 45%
                #     reward = 10
                # elif 91 <= random_reference < 161:  # 35%
                #     reward = 20
                # elif 161 <= random_reference < 191:  # 15%
                #     reward = 50
                # else:  # 5%
                #     reward = 100
                receiver = 贈與使用者
                self.real_logger.info(
                    f"{ctx.author.name}#{ctx.author.discriminator} 贈送 {receiver.name}#{receiver.discriminator}"
                    f" {reward} 點文字經驗值。"
                )
                receiver_embed = discord.Embed(
                    title="🎁收到贈禮！",
                    description=f"你收到來自{ctx.author.mention}的**`{reward}`點文字經驗值**贈禮！",
                    color=default_color,
                )
                receiver_embed.add_field(
                    name="回禮",
                    value="你可以在3小時內點擊下方按鈕，即可回送10點文字經驗值給對方作為回禮。\n" "放心，贈送回禮不會扣除你的經驗值！",
                    inline=False,
                )
                receiver_embed.set_footer(
                    text="贈禮加成！現在起，領取每日獎勵時指定「贈與使用者」，對方將更有機會獲得高點數獎勵！"
                )
                await receiver.send(
                    embed=receiver_embed,
                    view=self.GiftInTurn(ctx.author, self.real_logger),
                )
            else:  # 本人領取
                receiver = ctx.author
                if 1 <= random_reference < 101:  # 50%
                    reward = 10
                elif 101 <= random_reference < 141:  # 20%
                    reward = 20
                elif 141 <= random_reference < 171:  # 15%
                    reward = 50
                else:  # 15%
                    reward = 100
                # elif 101 <= random_reference < 181:  # 40%
                #     reward = 20
                # elif 181 <= random_reference < 196:  # 7.5%
                #     reward = 50
                # else:  # 2.5%
                #     reward = 100
            receiver_obj = json_assistant.User(receiver.id)
            receiver_obj.add_exp("text", reward)
            embed = discord.Embed(
                title="每日簽到",
                description=f"簽到成功！{receiver.mention}獲得*文字*經驗值`{reward}`點！",
                color=default_color,
            )
            json_assistant.User(ctx.author.id).set_last_daily_reward_claimed(
                time.time()
            )
            json_assistant.add_daily_reward_probability(reward)
            if receiver_obj.level_calc(
                "text"
            ) and receiver_obj.notify_threshold_reached("text"):
                self.real_logger.info(
                    f"等級提升：{receiver.name} 文字等級達到 {receiver_obj.get_level('text')} 等"
                )
                lvl_up_embed = discord.Embed(
                    title="等級提升",
                    description=f":tada:恭喜 {receiver.mention} *文字*等級升級到 "
                    f"**{receiver_obj.get_level('text')}** 等！",
                    color=default_color,
                )
                lvl_up_embed.set_thumbnail(url=receiver.display_avatar)
                await ctx.respond(embed=lvl_up_embed)
        daily_reward_prob_raw_data = json_assistant.get_daily_reward_probability()
        sum_of_rewards = 0
        rewards_list = []
        for i in daily_reward_prob_raw_data:
            rewards_list.append(int(i))
        rewards_list.sort()
        # 將所有獎勵次數加總
        for n in rewards_list:
            sum_of_rewards += daily_reward_prob_raw_data[str(n)]
        for j in rewards_list:
            # 列出所有點數獎勵出現的次數
            embed.add_field(
                name=f"{j}點",
                value=f"{daily_reward_prob_raw_data[str(j)]} 次 "
                f"({round(daily_reward_prob_raw_data[str(j)] / sum_of_rewards * 100, 1)} %)",
                inline=False,
            )
        embed.add_field(name="已領取獎勵數量", value=f"{sum_of_rewards} 次", inline=False)
        # embed.set_footer(text="贈禮加成！現在起，領取每日獎勵時指定「贈與使用者」，對方將更有機會獲得高點數獎勵！")
        embed.set_footer(text="為慶祝每日獎勵領取達到2000次，高點數獎勵的機率提升！")
        await ctx.respond(embed=embed, ephemeral=私人訊息)

    @discord.slash_command(
        name="musicdl", description="將影片下載為mp3。由於Discord有檔案大小限制，因此有時可能會失敗。"
    )
    async def dl(
        self,
        ctx,
        連結: Option(str, "欲下載的影片網址", required=True),  # noqa: PEP 3131
        加入後設資料: Option(  # noqa: PEP 3131
            bool, "是否在檔案中加入影片標題、作者與縮圖，會影響檔案的大小", required=False
        ) = False,
        位元率: Option(  # noqa: PEP 3131
            int,
            description="下載後，轉換為MP3時所使用的位元率，會影響檔案的大小與品質",
            choices=[96, 128, 160, 192, 256, 320],
            required=False,
        ) = 128,
    ):
        await ctx.defer()
        m_video = yt_download.Video(連結)
        if m_video.is_live():  # 排除直播影片
            embed = discord.Embed(
                title="此影片目前直播/串流中",
                description="你所提供的影片為直播且仍在串流中，無法下載。\n請在串流結束後再嘗試下載。",
                color=error_color,
            )
            embed.add_field(
                name="影片名稱", value=f"[{m_video.get_title()}]({連結})", inline=False
            )
            embed.set_image(url=m_video.get_thumbnail())
            await ctx.respond(embed=embed)
        else:
            length = m_video.get_length()
            if 加入後設資料:
                metadata = {
                    "title": m_video.get_title(),
                    "artist": m_video.get_uploader(),
                    "thumbnail_url": m_video.get_thumbnail(),
                }
            else:
                metadata = {}
            if length > 512:
                embed = discord.Embed(
                    title="影片長度過長",
                    description=f"影片長度(`{length}`秒)超過512秒，下載後可能無法成功上傳。是否仍要嘗試下載？",
                    color=error_color,
                )
                embed.add_field(
                    name="影片名稱", value=f"[{m_video.get_title()}]({連結})", inline=False
                )
                embed.add_field(name="影片長度", value=f"`{length}`秒", inline=False)
                embed.set_image(url=m_video.get_thumbnail())
                confirm_download = self.ConfirmDownload(
                    outer_instance=self,
                    video_instance=m_video,
                    metadata=metadata,
                    bit_rate=位元率,
                )
                await ctx.respond(embed=embed, view=confirm_download)
            else:
                if 加入後設資料:
                    embed = discord.Embed(
                        title="編輯後設資料",
                        description="請點擊下方按鈕，以編輯、確認後設資料。",
                        color=default_color,
                    )
                    embed.add_field(
                        name="為何會出現這則訊息？",
                        value="由於你使用指令時，將`加入後設資料`設為`True`。\n"
                        "如要忽略此步驟，請將`加入後設資料`設為`False`。",
                    )
                    await ctx.respond(
                        embed=embed,
                        view=Basics.MP3MetadataEditorView(
                            self,
                            m_video,
                            位元率,
                            metadata,
                        ),
                    )
                else:
                    embed = discord.Embed(
                        title="確認下載", description="已開始下載，請稍候。", color=default_color
                    )
                    embed.add_field(
                        name="影片名稱",
                        value=f"[{m_video.get_title()}]({連結})",
                        inline=False,
                    )
                    embed.add_field(name="影片長度", value=f"`{length}`秒", inline=False)
                    embed.set_image(url=m_video.get_thumbnail())
                    embed.set_footer(text="下載所需時間依影片長度、網路狀況及影片來源端而定。")
                    start_dl_message = await ctx.respond(embed=embed)
                    try:
                        await start_dl_message.edit(
                            file=await self.run_blocking(
                                self.bot,
                                self.ConfirmDownload.youtube_start_download,
                                m_video,
                                metadata,
                                位元率,
                            )
                        )
                    except Exception as e:
                        if "Request entity too large" in str(e):
                            embed = discord.Embed(
                                title="錯誤", description="檔案過大，無法上傳。", color=error_color
                            )
                            embed.add_field(
                                name="是否調整過位元率？",
                                value="如果你選擇了其他位元率，可能會導致檔案過大。請試著降低位元率。",
                                inline=False,
                            )
                            embed.add_field(
                                name="是否加入了後設資料？",
                                value="後設資料可能增加了檔案的大小。請試著將`加入後設資料`參數改為`False`。",
                                inline=False,
                            )
                            embed.add_field(
                                name="錯誤訊息", value=f"```{e}```", inline=False
                            )
                        else:
                            embed = discord.Embed(
                                title="錯誤", description="發生未知錯誤。", color=error_color
                            )
                            embed.add_field(
                                name="錯誤訊息", value=f"```{e}```", inline=False
                            )
                        await start_dl_message.edit(embed=embed)

    @discord.slash_command(
        name="rc", description="重新連接至語音頻道。可指定頻道，否則將自動檢測音樂機器人及Allen Why在哪個頻道並加入。"
    )
    async def rc(
        self,
        ctx,
        頻道: Option(discord.VoiceChannel, "指定要加入的頻道", required=False),  # noqa: PEP 3131
        私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False,  # noqa: PEP 3131
    ):
        if 頻道 is None:
            result = await self.check_voice_channel()
            if isinstance(result, int):
                embed = discord.Embed(
                    title="已加入頻道",
                    description=f"已經自動加入了 <#{result}>！",
                    color=default_color,
                )
            elif isinstance(result, str):
                embed = discord.Embed(
                    title="錯誤", description=f"發生錯誤：`{result}`", color=error_color
                )
            elif result is None:
                embed = discord.Embed(
                    title="錯誤",
                    description="找不到<@885723595626676264>及<@657519721138094080>在哪個頻道。",
                    color=error_color,
                )
            else:
                embed = discord.Embed(
                    title="錯誤", description="發生未知錯誤。", color=error_color
                )
        else:
            try:
                await 頻道.guild.change_voice_state(channel=頻道)
                embed = discord.Embed(
                    title="已加入頻道", description=f"已經加入了 <#{頻道.id}>！", color=default_color
                )
            except Exception as e:
                embed = discord.Embed(
                    title="錯誤", description=f"發生錯誤：`{e}`", color=error_color
                )
        await ctx.respond(embed=embed, ephemeral=私人訊息)

    @discord.slash_command(name="dc", description="從目前的語音頻道中斷連接。")
    async def dc(
        self,
        ctx,
        私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False,  # noqa: PEP 3131
    ):
        try:
            await ctx.guild.change_voice_state(channel=None)
            embed = discord.Embed(
                title="已斷開連接", description="已經從語音頻道中斷連接。", color=default_color
            )
        except Exception as e:
            if str(e) == "'NoneType' object has no attribute 'disconnect'":
                embed = discord.Embed(
                    title="錯誤", description="目前沒有連接到任何語音頻道。", color=error_color
                )
            else:
                embed = discord.Embed(
                    title="錯誤", description=f"發生錯誤：`{e}`", color=error_color
                )
        await ctx.respond(embed=embed, ephemeral=私人訊息)

    async def check_voice_channel(self):
        # 列出所有語音頻道
        voice_channel_lists = []
        for server in self.bot.guilds:
            for channel in server.channels:
                if channel.type == discord.ChannelType.voice:
                    voice_channel_lists.append(channel)
                    self.real_logger.debug(f"找到語音頻道：{server.name}/{channel.name}")
                    members = channel.members
                    # 列出所有語音頻道的成員
                    for member in members:
                        self.real_logger.debug(f"   ⌊{member.name}")
                        if (
                            member.id == 885723595626676264
                            or member.id == 657519721138094080
                        ):
                            # 若找到Allen Music Bot或Allen Why，則嘗試加入該語音頻道
                            try:
                                await channel.guild.change_voice_state(
                                    channel=channel, self_mute=True, self_deaf=True
                                )
                                return channel.id
                            except Exception as e:
                                if str(e) == "Already connected to a voice channel.":
                                    return "已經連線至語音頻道。"
                                else:
                                    return str(e)


class Events(commands.Cog):
    def __init__(self, bot: commands.Bot, real_logger: logger.CreateLogger):
        self.bot = bot
        self.real_logger = real_logger

    class GetTmpRole(discord.ui.View):
        def __init__(self, outer_instance):
            super().__init__()
            self.outer_instance = outer_instance
            self.bot = outer_instance.bot
            self.real_logger = outer_instance.real_logger

        @discord.ui.button(
            label="取得臨時身分組", style=discord.ButtonStyle.blurple, emoji="✨"
        )
        async def confirm(
            self, button: discord.ui.Button, interaction: discord.Interaction
        ):
            self.real_logger.debug(f"{interaction.user.name} 按下了「取得臨時身分組」按鈕")
            server = self.bot.get_guild(857996539262402570)
            try:
                button.disabled = True
                user_member_obj = server.get_member(interaction.user.id)
                await user_member_obj.add_roles(
                    discord.utils.get(server.roles, id=1083536792717885522)
                )
                self.real_logger.debug(f"成功將 {interaction.user.name} 加入臨時身分組")
                embed = discord.Embed(
                    title="取得臨時身分組成功！",
                    description="已經將你加入臨時身分組！你可以查看文字頻道的內容，但是不能參與對談。",
                    color=0x57C2EA,
                )
                await interaction.response.edit_message(embed=embed, view=self)
            except Exception as e:
                self.real_logger.error(f"將 {interaction.user.name} 加入臨時身分組時發生錯誤")
                self.real_logger.error(str(e))
                embed = discord.Embed(
                    title="取得臨時身分組失敗！",
                    description=f"請聯絡管理員。\n錯誤訊息：\n```{e}```",
                    color=error_color,
                )
                embed.set_footer(text="聯絡管理員時，請提供錯誤訊息以做為參考。")
                await interaction.response.send_message(embed=embed)

    class GetRealName(discord.ui.Modal):
        def __init__(self, outer_instance) -> None:
            super().__init__(title="審核", timeout=None)

            self.add_item(
                discord.ui.InputText(
                    style=discord.InputTextStyle.short,
                    label="請輸入你的真實姓名",
                    max_length=20,
                    required=True,
                )
            )
            self.bot = outer_instance.bot

        async def callback(self, interaction: discord.Interaction):
            embed = discord.Embed(
                title="已提交新的審核要求！", description="你的回應已送出！請等待管理員的審核。", color=0x57C2EA
            )
            embed.add_field(
                name="你的帳號名稱",
                value=f"{interaction.user.name}#{interaction.user.discriminator}",
                inline=False,
            )
            embed.add_field(name="你的回應", value=self.children[0].value, inline=False)
            await interaction.response.edit_message(embed=embed, view=None)
            embed = discord.Embed(
                title="收到新的審核要求", description="有新的審核要求，請盡快處理。", color=0x57C2EA
            )
            embed.set_thumbnail(url=interaction.user.display_avatar)
            embed.add_field(
                name="帳號名稱", value=f"<@{interaction.user.id}>", inline=False
            )
            embed.add_field(name="真實姓名", value=self.children[0].value, inline=False)
            await self.bot.get_channel(1114444831054376971).send(
                content="@everyone", embed=embed
            )

    class VerificationModalToView(discord.ui.View):
        def __init__(self, outer_instance):
            super().__init__()
            self.outer_instance = outer_instance

        @discord.ui.button(label="點此開始審核", style=discord.ButtonStyle.green, emoji="📝")
        async def button_callback(
            self, button: discord.ui.Button, interaction: discord.Interaction
        ):
            await interaction.response.send_modal(
                self.outer_instance.GetRealName(self.outer_instance)
            )

    @staticmethod
    def get_year_process():
        # 若今年為閏年則將year_to_sec改為31622400，否則設為31536000
        current_year = datetime.datetime.now(tz=now_tz).year
        if current_year % 400 == 0:
            year_to_sec = 31622400
        elif current_year % 4 == 0 and current_year % 100 != 0:
            year_to_sec = 31622400
        else:
            year_to_sec = 31536000
        jun_1st = datetime.datetime.timestamp(
            datetime.datetime.strptime(f"{current_year}/01/01", "%Y/%m/%d").replace(
                tzinfo=now_tz
            )
        )
        year_process_sec = time.time() - jun_1st
        year_process = floor((year_process_sec / year_to_sec) * 10000) / 100
        return year_process

    @tasks.loop(seconds=1)
    async def set_presence_as_year_process(self):
        year_process = self.get_year_process()
        current_year = datetime.datetime.now(tz=now_tz).year
        if datetime.datetime.now(tz=now_tz).second == 0:
            activity = discord.Activity(
                name=f"{current_year}年進度：{year_process} % 完成！",
                type=discord.ActivityType.watching,
            )
            await self.bot.change_presence(
                activity=activity, status=discord.Status.online
            )
        elif datetime.datetime.now(tz=now_tz).second == 30:
            activity = discord.Activity(
                name=get_RPC_context(), type=discord.ActivityType.playing
            )
            await self.bot.change_presence(
                activity=activity, status=discord.Status.online
            )

    @tasks.loop(seconds=10)
    async def give_voice_exp(self):  # 給予語音經驗
        exclude_channel = [888707777659289660, 1076702101964599337]
        for server in self.bot.guilds:
            for channel in server.channels:
                if (
                    channel.type == discord.ChannelType.voice
                    and channel.id not in exclude_channel
                ):
                    members = channel.members
                    active_human_members = []
                    for member in members:  # 將機器人、靜音/拒聽的成員排除
                        if (
                            not member.bot
                            and not member.voice.self_mute
                            and not member.voice.self_deaf
                        ):
                            active_human_members.append(member)
                    for member in active_human_members:
                        exp_report: dict = exp_reports_list.get(member.id, deepcopy(exp_report_template))
                        if len(active_human_members) > 1:  # 若語音頻道人數大於1
                            value = 1 + len(active_human_members) / 10
                            exp_report["time_exp"] += value
                            for a in member.activities:
                                if isinstance(a, discord.Activity):
                                    value += 0.1
                                    exp_report["activity_bonus"] += 0.1
                            value = floor(value * 10) / 10
                            member_obj = json_assistant.User(member.id)
                            member_obj.add_exp("voice", value)
                            self.real_logger.info(f"獲得經驗值：{member.name} 獲得語音經驗 {value}")
                            if member_obj.level_calc("voice"):
                                self.real_logger.info(
                                    f"等級提升：{member.name} 語音等級"
                                    f"達到 {member_obj.get_level('voice')} 等"
                                )
                                if member_obj.notify_threshold_reached("voice"):
                                    embed = discord.Embed(
                                        title="等級提升",
                                        description=f":tada:恭喜 <@{member.id}> *語音*等級升級到 "
                                        f"**{member_obj.get_level('voice')}**"
                                        f" 等！",
                                        color=default_color,
                                    )
                                    embed.set_thumbnail(url=member.display_avatar)
                                    embed.set_footer(
                                        text="關於經驗值計算系統，請輸入/user_info about"
                                    )
                                    await member.send(embed=embed)
                            for m in active_human_members:
                                if (
                                    m.id not in exp_report["partners"]
                                    and m.id != member.id
                                ):
                                    exp_report["partners"].append(m.id)
                            if member_obj.get_exp_report_enabled():
                                exp_reports_list[member.id] = exp_report

    @staticmethod
    def convert_seconds(seconds: int) -> str:
        hours = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        return f"`{hours}` 小時 `{minutes}` 分 `{seconds}` 秒"

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if json_assistant.User(member.id).get_exp_report_enabled():
            if after.channel is None:  # 中斷語音連線
                self.real_logger.debug(f"{member.name} 結束了語音階段：{before.channel.name}")
                if member.id in exp_reports_list.keys():
                    report = exp_reports_list.pop(member.id)
                    if report["time_exp"] == 0 and report["activity_bonus"] == 0:
                        self.real_logger.debug(
                            f"語音階段中未獲得任何語音經驗值，因此不傳送報告給 {member.name}"
                        )
                        return
                    time_delta = int(time.time()) - report["join_at"]
                    embed = discord.Embed(
                        title="語音經驗值報告",
                        description="👋剛才語音階段的的經驗值報告如下！",
                        color=default_color,
                    )
                    embed.add_field(
                        name="開始於", value=f"<t:{report['join_at']}>", inline=True
                    )
                    embed.add_field(
                        name="結束於", value=f"<t:{int(time.time())}>", inline=True
                    )
                    embed.add_field(
                        name="總時長", value=self.convert_seconds(time_delta), inline=True
                    )
                    channel_str, partner_str = "", ""
                    for c in report["channels"]:
                        c = "<#" + str(c) + ">"
                        channel_str += c
                    if member.id in report["partners"]:
                        report["partners"].remove(member.id)
                    for m in report["partners"]:
                        if m == member.id:
                            continue
                        m = "<@" + str(m) + ">"
                        partner_str += m
                    embed.add_field(
                        name=f"加入過的頻道 (共{len(report['channels'])}個)",
                        value=channel_str,
                        inline=False,
                    )
                    embed.add_field(
                        name=f"與你互動過的使用者 (共{len(report['partners'])}位)",
                        value=partner_str,
                        inline=False,
                    )
                    embed.add_field(
                        name="時間點數 (因待在語音頻道而獲得的點數)",
                        value=f"`{floor(report['time_exp']*10)/10}` 點",
                        inline=False,
                    )
                    embed.add_field(
                        name="活動加成 (因進行遊戲、聆聽Spotify等而額外獲得的點數)",
                        value=f"`{floor(report['activity_bonus']*10)/10}` 點",
                        inline=False,
                    )
                    embed.set_footer(
                        text="目前此功能測試中。如要停用此功能，請使用/user_info set_voice_exp_report指令。"
                    )
                    await member.send(embed=embed)
            elif (
                before.channel is not None and before.channel.id != after.channel.id
            ):  # 加入其他頻道
                self.real_logger.debug(
                    f"{member.name} 加入了其他頻道：{before.channel.name} -> {after.channel.name}"
                )
                report = exp_reports_list.get(member.id, deepcopy(exp_report_template))
                report["channels"].append(after.channel.id)
                exp_reports_list[member.id] = report
            elif before.channel is None and after.channel is not None:  # 開始語音階段
                self.real_logger.debug(f"{member.name} 開始了語音階段：{after.channel.name}")
                report = exp_reports_list.get(member.id, deepcopy(exp_report_template))
                report["join_at"] = int(time.time())
                report["channels"].append(after.channel.id)
                exp_reports_list[member.id] = report

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_joined = member.guild
        embed = discord.Embed(
            title="歡迎新成員！",
            description=f"歡迎{member.mention}加入**{member.guild}**！",
            color=0x16D863,
        )
        join_date = member.joined_at.astimezone(tz=now_tz).strftime("%Y-%m-%d %H:%M:%S")
        embed.set_footer(text=f"於 {join_date} 加入")
        embed.set_thumbnail(url=member.display_avatar)
        await guild_joined.system_channel.send(embed=embed)
        json_assistant.User(member.id).set_join_date(join_date)
        new_member = await self.bot.fetch_user(member.id)
        if guild_joined.id == 857996539262402570:
            embed = discord.Embed(
                title=f"歡迎加入 {member.guild.name} ！",
                description="請到[這裡](https://discord.com/channels/857996539262402570/858373026960637962)查看頻道介紹。",
                color=0x57C2EA,
            )
            await new_member.send(embed=embed)
            embed = discord.Embed(
                title="在開始之前...",
                description="什麼頻道都沒看到嗎？這是因為你**並未被分配身分組**。但是放心，我們會盡快確認你的身分，到時你就能加入我們了！",
                color=0x57C2EA,
            )
            await new_member.send(embed=embed)
            # embed = discord.Embed(
            #     title="取得臨時身分組", description="在取得正式身分組前，請點擊下方按鈕取得臨時身分組。", color=0x57C2EA
            # )
            # await new_member.send(embed=embed, view=self.GetTmpRole(self))
        elif guild_joined.id == 1114203090950836284:
            embed = discord.Embed(
                title=f"歡迎加入 {member.guild.name} ！",
                description="在正式加入此伺服器前，請告訴我們你的**真名**，以便我們授予你適當的權限！",
                color=0x57C2EA,
            )
            try:
                await new_member.send(
                    embed=embed, view=self.VerificationModalToView(self)
                )
            except discord.errors.HTTPException as error:
                if error.code == 50007:
                    await guild_joined.system_channel.send(
                        f"{member.mention}，由於你的私人訊息已關閉，無法透過機器人進行快速審核。\n"
                        f"請私訊管理員你的**真名**，以便我們授予你適當的身分組！"
                    )
                else:
                    raise error

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        embed = discord.Embed(
            title="有人離開了我們...",
            description=f"{member.name} 離開了 **{member.guild}** ...",
            color=0x095997,
        )
        leave_date = datetime.datetime.now(tz=now_tz).strftime("%Y-%m-%d %H:%M:%S")
        embed.set_footer(text=f"於 {leave_date} 離開")
        await member.guild.system_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_application_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="指令冷卻中",
                description=f"這個指令正在冷卻中，請在`{round(error.retry_after)}`秒後再試。",
                color=error_color,
            )
            await ctx.respond(embed=embed, ephemeral=True)
        elif isinstance(error, commands.NotOwner):
            embed = discord.Embed(
                title="錯誤", description="你沒有權限使用此指令。", color=error_color
            )
            await ctx.respond(embed=embed, ephemeral=True)
        elif isinstance(error, discord.errors.Forbidden) or isinstance(
            error, discord.errors.HTTPException
        ):
            self.real_logger.warning("無法傳送贈禮通知給對方，因為該用戶已關閉私人訊息。")
            embed = discord.Embed(
                title="錯誤",
                description="糟糕！對方似乎已關閉「允許陌生人傳送陌生訊息」功能，你的贈禮無法送達！",
                color=default_color,
            )
            embed.add_field(
                name="疑難排解",
                value="請參考[這則文章]"
                "(https://support.discord.com/hc/zh-tw/articles/7924992471191-"
                "%E8%A8%8A%E6%81%AF%E8%AB%8B%E6%B1%82)來解決此問題後重試。",
            )
            await ctx.respond(embed=embed, ephemeral=True)
        else:
            raise error

    @commands.Cog.listener()
    async def on_ready(self):
        self.real_logger.info("機器人準備完成！")
        self.real_logger.info(f"PING值：{round(self.bot.latency * 1000)}ms")
        self.real_logger.info(
            f"登入身分：{self.bot.user.name}#{self.bot.user.discriminator}"
        )
        normal_activity = discord.Activity(
            name=get_RPC_context(), type=discord.ActivityType.playing
        )
        await self.bot.change_presence(
            activity=normal_activity, status=discord.Status.online
        )
        self.give_voice_exp.start()
        self.set_presence_as_year_process.start()
        # await check_voice_channel()

    @commands.Cog.listener()
    async def on_application_command(self, ctx):
        cmd = (
            f"{ctx.command.parent.name} {ctx.command.name}"
            if ctx.command.parent
            else ctx.command.name
        )
        self.real_logger.info(f'{ctx.author} 執行了斜線指令 "{cmd}"')

    async def check_voice_channel(self) -> int | str:
        # 列出所有語音頻道
        voice_channel_lists = []
        for server in self.bot.guilds:
            for channel in server.channels:
                if channel.type == discord.ChannelType.voice:
                    voice_channel_lists.append(channel)
                    self.real_logger.debug(f"找到語音頻道：{server.name}/{channel.name}")
                    members = channel.members
                    # 列出所有語音頻道的成員
                    for member in members:
                        self.real_logger.debug(f"   ⌊{member.name}")
                        if (
                            member.id == 885723595626676264
                            or member.id == 657519721138094080
                        ):
                            # 若找到Allen Music Bot或Allen Why，則嘗試加入該語音頻道
                            try:
                                await channel.guild.change_voice_state(
                                    channel=channel, self_mute=True, self_deaf=True
                                )
                                return channel.id
                            except Exception as e:
                                if str(e) == "Already connected to a voice channel.":
                                    return "已經連線至語音頻道。"
                                else:
                                    return str(e)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id == self.bot.user.id:
            return
        msg_in = message.content
        exclude_channels = [
            1035754607286169631,
        ]
        music_cmd_channels = [
            891665312028713001,  # 貓娘實驗室/音樂指令區
            1114523541312897034,  # FRC7636/指令區
            1248646014798397491,  # 野人集中營/music
            1249352023615344671,  # 損友俱樂部/丟song
        ]
        exclude_channels += music_cmd_channels
        if message.channel.id in music_cmd_channels:
            if (
                msg_in.startswith("https://www.youtube.com")
                or msg_in.startswith("https://youtu.be")
                or msg_in.startswith("https://m.youtube.com")
                or msg_in.startswith("https://youtube.com")
                or msg_in.startswith("https://open.spotify.com")
                or msg_in.startswith("https://music.youtube.com")
            ):
                check_vc_result = await self.check_voice_channel()
                if isinstance(check_vc_result, str):
                    await message.channel.send(
                        "**注意：機器人自動加入語音頻道時失敗。音樂機器人可能會回傳錯誤。**", delete_after=5
                    )
                if "&list=" in msg_in:
                    msg_in = msg_in[: msg_in.find("&list=")]
                    await message.reply(
                        f"{message.author.mention} 偵測到此連結來自播放清單！已轉換為單一影片連結。",
                        delete_after=5,
                    )
                elif "?list=" in msg_in:
                    msg_in = msg_in[: msg_in.find("?list=")]
                    await message.reply(
                        f"{message.author.mention} 偵測到此連結來自播放清單！已轉換為單一影片連結。",
                        delete_after=5,
                    )
                ap_cmd = "ap!p " + msg_in
                await message.channel.send(ap_cmd, delete_after=3)
                await message.add_reaction("✅")
                return
        if message.channel.id in exclude_channels:
            return
        member_obj = json_assistant.User(message.author.id)
        time_delta = time.time() - member_obj.get_last_active_time()
        if time_delta < 300:
            return
        if "Direct Message" in str(message.channel):
            embed = discord.Embed(
                title="是不是傳錯人了...？", description="很抱歉，目前本機器人不接受私人訊息。", color=error_color
            )
            await message.channel.send(embed=embed)
            return
        if not message.author.bot and isinstance(msg_in, str):
            if len(msg_in) <= 15:
                self.real_logger.info(
                    f"獲得經驗值：{message.author.name} 文字經驗值 +{len(msg_in)} (訊息長度：{len(msg_in)})"
                )
                member_obj.add_exp("text", len(msg_in))
            else:
                member_obj.add_exp("text", 15)
                self.real_logger.info(
                    f"獲得經驗值：{message.author.name} 文字經驗值 +15 (訊息長度：{len(msg_in)})"
                )
        member_obj.set_last_active_time(time.time())
        if member_obj.level_calc("text") and member_obj.notify_threshold_reached(
            "text"
        ):
            self.real_logger.info(
                f"等級提升：{message.author.name} 文字等級"
                f"達到 {member_obj.get_level('text')} 等"
            )
            embed = discord.Embed(
                title="等級提升",
                description=f":tada:恭喜 <@{message.author.id}> *文字*等級升級到 "
                f"**{member_obj.get_level('text')}** 等！",
                color=default_color,
            )
            embed.set_thumbnail(url=message.author.display_avatar)
            embed.set_footer(text="關於經驗值計算系統，請輸入/user_info about")
            await message.channel.send(embed=embed, delete_after=5)


def setup(bot):
    bot.add_cog(Basics(bot, bot.logger))
    bot.logger.info('"Basics"已被載入。')
    bot.add_cog(Events(bot, bot.logger))
    bot.logger.info('"Events"已被載入。')
