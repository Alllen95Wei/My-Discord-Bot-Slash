# coding: utf-8
import discord
from discord.ext import commands
from discord.ext import tasks
from discord import Option
import git
import os
import time
import datetime
import zoneinfo
from dotenv import load_dotenv
from random import choice
from random import randint
from shlex import split
from subprocess import run
from platform import system
from PIL import ImageGrab
import logging
from colorlog import ColoredFormatter
import typing
import functools

from youtube_to_mp3 import main_dl
import youtube_download as yt_download
import detect_pc_status
import update as upd
import json_assistant
from read_RPC import get_RPC_context
from bullshit import bullshit

# 機器人
intents = discord.Intents.all()
bot = commands.Bot(intents=intents, help_command=None)
# 常用物件、變數
base_dir = os.path.abspath(os.path.dirname(__file__))
default_color = 0x5FE1EA
error_color = 0xF1411C
exp_enabled = True
last_chat_used_time = 0
now_tz = zoneinfo.ZoneInfo("Asia/Taipei")
normal_activity = discord.Activity(name=get_RPC_context(), type=discord.ActivityType.playing)
# 載入TOKEN
load_dotenv(dotenv_path=os.path.join(base_dir, "TOKEN.env"))
TOKEN = str(os.getenv("TOKEN"))


class CreateLogger:
    def __init__(self):
        super().__init__()
        self.c_logger = self.color_logger()
        self.a_logger = self.anonymous_logger()
        logging.addLevelName(25, "ANONYMOUS")

    @staticmethod
    def color_logger():
        formatter = ColoredFormatter(
            fmt="%(white)s[%(asctime)s] %(log_color)s%(levelname)-10s%(reset)s %(blue)s%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            reset=True,
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "ANONYMOUS": "purple",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red",
            },
        )

        logger = logging.getLogger()
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        log_path = os.path.join(base_dir, "logs",
                                f"logs {datetime.datetime.now(tz=now_tz).strftime('%Y.%m.%d %H.%M.%S')}.log")
        with open(log_path, "w"):
            pass
        f_handler = logging.FileHandler(log_path, encoding="utf-8")
        f_handler.setFormatter(formatter)
        logger.addHandler(f_handler)
        logger.setLevel(logging.DEBUG)

        return logger

    @staticmethod
    def anonymous_logger():
        formatter = logging.Formatter(
            fmt="[%(asctime)s] %(levelname)-8s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S")

        logger = logging.getLogger("anonymous_logger")
        handler = logging.FileHandler("anonymous.log", encoding="utf-8")
        handler.setLevel(25)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def debug(self, message: str):
        self.c_logger.debug(message)

    def info(self, message: str):
        self.c_logger.info(message)

    def warning(self, message: str):
        self.c_logger.warning(message)

    def error(self, message: str):
        self.c_logger.error(message)

    def critical(self, message: str):
        self.c_logger.critical(message)

    def anonymous(self, message: str):
        self.c_logger.log(25, message)
        self.a_logger.log(25, message)


# 建立logger
real_logger = CreateLogger()


@tasks.loop(seconds=10)
async def give_voice_exp() -> None:  # 給予語音經驗
    exclude_channel = [888707777659289660, 1076702101964599337]
    for server in bot.guilds:
        for channel in server.channels:
            if channel.type == discord.ChannelType.voice and channel.id not in exclude_channel:
                members = channel.members
                active_human_members = []
                for member in members:  # 將機器人、靜音/拒聽的成員排除
                    if not member.bot and not member.voice.self_mute and not member.voice.self_deaf:
                        active_human_members.append(member)
                for member in active_human_members:
                    if exp_enabled:
                        if len(active_human_members) > 1:  # 若語音頻道人數大於1
                            value = 1 + len(active_human_members) / 10
                            for a in member.activities:
                                if isinstance(a, discord.Activity):
                                    value += 0.1
                            json_assistant.add_exp(member.id, "voice", value)
                            real_logger.info(f"獲得經驗值：{member.name} 獲得語音經驗 {value}")
                            if json_assistant.level_calc(member.id, "voice"):
                                real_logger.info(f"等級提升：{member.name} 語音等級"
                                                 f"達到 {json_assistant.get_level(member.id, 'voice')} 等")
                                embed = discord.Embed(title="等級提升",
                                                      description=f":tada:恭喜 <@{member.id}> *語音*等級升級到 "
                                                                  f"**{json_assistant.get_level(member.id, 'voice')}**"
                                                                  f" 等！",
                                                      color=default_color)
                                embed.set_thumbnail(url=member.display_avatar)
                                embed.set_footer(text="關於經驗值計算系統，請輸入/user_info about")
                                await member.send(embed=embed)


async def check_voice_channel():
    # 列出所有語音頻道
    voice_channel_lists = []
    for server in bot.guilds:
        for channel in server.channels:
            if channel.type == discord.ChannelType.voice:
                voice_channel_lists.append(channel)
                real_logger.debug(f"找到語音頻道：{server.name}/{channel.name}")
                members = channel.members
                # msg = ""
                # 列出所有語音頻道的成員
                for member in members:
                    real_logger.debug(f"   ⌊{member.name}")
                    if member == bot.get_user(885723595626676264) or member == bot.get_user(657519721138094080):
                        # 若找到Allen Music Bot或Allen Why，則嘗試加入該語音頻道
                        try:
                            await channel.guild.change_voice_state(channel=channel, self_mute=True, self_deaf=True)
                            # msg = "加入語音頻道：" + server.name + "/" + channel.name
                            # log_writter.write_log(msg)
                            return channel.id
                        except Exception as e:
                            # msg = "加入語音頻道失敗：" + server.name + "/" + channel.name + "(" + str(e) + ")"
                            # log_writter.write_log(msg)
                            if str(e) == "Already connected to a voice channel.":
                                return "已經連線至語音頻道。"
                            else:
                                return str(e)
                    else:
                        return None


def get_year_process():
    year_to_sec = 31449600
    jun_1st = datetime.datetime.timestamp(
                datetime.datetime.strptime("2023/01/01", "%Y/%m/%d").replace(tzinfo=now_tz))
    year_process_sec = time.time() - jun_1st
    year_process = round((year_process_sec / year_to_sec) * 100, 2)
    return year_process


@tasks.loop(minutes=5)
async def set_presence_as_year_process():
    year_process = get_year_process()
    current_year = datetime.datetime.strftime(datetime.datetime.now(tz=now_tz), "%Y")
    activity = discord.Activity(name=f"{current_year}年進度：{year_process} % 完成！", type=discord.ActivityType.watching)
    await bot.change_presence(activity=activity, status=discord.Status.online)


# def get_tmp_role():  # credit: 鄭詠鴻
#     btn = discord.ui.Button(style=discord.ButtonStyle.primary, label="取得臨時身分組", emoji="✨")
#
#     async def btn_callback(self, button, interaction: discord.Interaction):
#         server = await bot.fetch_guild(857996539262402570)
#         try:
#             button.disabled = True
#             await interaction.user.add_roles(discord.utils.get(server.roles, id=1083536792717885522))
#             embed = discord.Embed(
#                 title="取得臨時身分組成功！",
#                 description="已經將你加入臨時身分組！你可以查看文字頻道的內容，但是不能參與對談。",
#                 color=0x57c2ea)
#             await interaction.response.edit_message(view=self)
#             await interaction.response.send_message(embed=embed)
#         except Exception as e:
#             embed = discord.Embed(
#                 title="取得臨時身分組失敗！",
#                 description=f"請聯絡管理員。\n錯誤訊息：\n```{e}```",
#                 color=error_color)
#             embed.set_footer(text="聯絡管理員時，請提供錯誤訊息以做為參考。")
#             await interaction.response.send_message(embed=embed)
#     btn.callback = btn_callback
#
#     view = discord.ui.View()
#     view.add_item(btn)
#     return view


class GetTmpRole(discord.ui.View):
    @discord.ui.button(label="取得臨時身分組", style=discord.ButtonStyle.blurple, emoji="✨")
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        real_logger.debug(f"{interaction.user.name} 按下了「取得臨時身分組」按鈕")
        server = bot.get_guild(857996539262402570)
        try:
            button.disabled = True
            user_member_obj = server.get_member(interaction.user.id)
            await user_member_obj.add_roles(discord.utils.get(server.roles, id=1083536792717885522))
            real_logger.debug(f"成功將 {interaction.user.name} 加入臨時身分組")
            embed = discord.Embed(
                title="取得臨時身分組成功！",
                description="已經將你加入臨時身分組！你可以查看文字頻道的內容，但是不能參與對談。",
                color=0x57c2ea)
            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            real_logger.error(f"將 {interaction.user.name} 加入臨時身分組時發生錯誤")
            real_logger.error(str(e))
            embed = discord.Embed(
                title="取得臨時身分組失敗！",
                description=f"請聯絡管理員。\n錯誤訊息：\n```{e}```",
                color=error_color)
            embed.set_footer(text="聯絡管理員時，請提供錯誤訊息以做為參考。")
            await interaction.response.send_message(embed=embed)


class GiftInTurn(discord.ui.View):
    def __init__(self, giver: [discord.User, discord.Member]):
        super().__init__(timeout=3600)
        self.giver = giver

    @discord.ui.button(label="回送10點作為感謝(不會扣除你的經驗值！)", style=discord.ButtonStyle.blurple, emoji="🎁")
    async def gift_btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        button.disabled = True
        json_assistant.add_exp(self.giver.id, "text", 10)
        embed = discord.Embed(title="已送出回禮！", description=f"你已贈送{self.giver.mention}**10點文字經驗值**作為回禮！"
                              , color=default_color)
        await interaction.response.edit_message(embed=embed, view=self)
        giver_embed = discord.Embed(title="收到回禮！", description=f"{interaction.user.mention}送你**10點文字經驗值**作為回禮！"
                                    , color=default_color)
        try:
            await self.giver.send(embed=giver_embed)
        except discord.errors.Forbidden:
            real_logger.warning(f"無法傳送回禮通知給 {self.giver.name}#{self.giver.discriminator}，因為該用戶已關閉私人訊息。")


class GetRealName(discord.ui.Modal):
    def __init__(self) -> None:
        super().__init__(title="審核", timeout=None)

        self.add_item(discord.ui.InputText(style=discord.InputTextStyle.short,
                                           label="請輸入你的真實姓名", max_length=20, required=True))

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title="已提交新的審核要求！", description="你的回應已送出！請等待管理員的審核。", color=0x57c2ea)
        embed.add_field(name="你的帳號名稱", value=f"{interaction.user.name}#{interaction.user.discriminator}", inline=False)
        embed.add_field(name="你的回應", value=self.children[0].value, inline=False)
        await interaction.response.edit_message(embed=embed, view=None)
        embed = discord.Embed(title="收到新的審核要求", description="有新的審核要求，請盡快處理。", color=0x57c2ea)
        embed.set_thumbnail(url=interaction.user.display_avatar)
        embed.add_field(name="帳號名稱", value=f"<@{interaction.user.id}>", inline=False)
        embed.add_field(name="真實姓名", value=self.children[0].value, inline=False)
        server = bot.get_guild(857996539262402570)
        await bot.get_channel(1114444831054376971).send(embed=embed, view=GiveRole(server.get_member(interaction.user.id
                                                                                                     )))


class VerificationModalToView(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="點此開始審核", style=discord.ButtonStyle.green, emoji="📝")
    async def button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(GetRealName())


class GiveRole(discord.ui.View):
    def __init__(self, member: discord.Member):
        super().__init__(timeout=None)
        self.server = bot.get_guild(1114203090950836284)
        self.server_roles = self.server.roles
        self.member = member

    @discord.ui.button(label="高一", style=discord.ButtonStyle.green, emoji="1️⃣", row=0)
    async def grade1(self, button: discord.ui.Button, interaction: discord.Interaction):
        grade1_role = self.server.get_role(1114212978707923167)
        await self.member.add_roles(grade1_role)
        await interaction.followup.send(f"已經將 {self.member.mention} 加入 {grade1_role.mention} 身分組！")
        embed = discord.Embed(title="身分組更新！", description=f"你已加入 {grade1_role.name} 身分組。", color=grade1_role.color)
        await self.member.send(embed=embed)

    @discord.ui.button(label="高二", style=discord.ButtonStyle.green, emoji="2️⃣", row=0)
    async def grade2(self, button: discord.ui.Button, interaction: discord.Interaction):
        grade2_role = self.server.get_role(1114212714634559518)
        print(type(grade2_role))
        await self.member.add_roles(grade2_role, reason="由管理員透過機器人分配")
        await interaction.followup.send(f"已經將 {self.member.mention} 加入 {grade2_role.mention} 身分組！")
        embed = discord.Embed(title="身分組更新！", description=f"你已加入 {grade2_role.name} 身分組。", color=grade2_role.color)
        await self.member.send(embed=embed)

    @discord.ui.button(label="老人", style=discord.ButtonStyle.green, emoji="🧓", row=0)
    async def senior(self, button: discord.ui.Button, interaction: discord.Interaction):
        senior_role = discord.utils.get(self.server_roles, id=1114223380535709767)
        await self.member.add_roles(senior_role)
        await interaction.followup.send(f"已經將 {self.member.mention} 加入 {senior_role.mention} 身分組！")
        embed = discord.Embed(title="身分組更新！", description=f"你已加入 {senior_role.name} 身分組。", color=senior_role.color)
        await self.member.send(embed=embed)

    @discord.ui.button(label="策略組", style=discord.ButtonStyle.blurple, emoji="🧠", row=1)
    async def strategy(self, button: discord.ui.Button, interaction: discord.Interaction):
        strategy_role = discord.utils.get(self.server_roles, id=1114204480976719982)
        await self.member.add_roles(strategy_role)
        await interaction.followup.send(f"已經將 {self.member.mention} 加入 {strategy_role.mention} 身分組！")
        embed = discord.Embed(title="身分組更新！", description=f"你已加入 {strategy_role.name} 身分組。", color=strategy_role.color)
        await self.member.send(embed=embed)

    @discord.ui.button(label="機構組", style=discord.ButtonStyle.blurple, emoji="⚙️", row=1)
    async def mechanism(self, button: discord.ui.Button, interaction: discord.Interaction):
        mechanism_role = discord.utils.get(self.server_roles, id=1114204794509348947)
        await self.member.add_roles(mechanism_role)
        await interaction.followup.send(f"已經將 {self.member.mention} 加入 {mechanism_role.mention} 身分組！")
        embed = discord.Embed(title="身分組更新！", description=f"你已加入 {mechanism_role.name} 身分組。",
                              color=mechanism_role.color)
        await self.member.send(embed=embed)

    @discord.ui.button(label="電資組", style=discord.ButtonStyle.blurple, emoji="⚡", row=1)
    async def electric(self, button: discord.ui.Button, interaction: discord.Interaction):
        electric_role = discord.utils.get(self.server_roles, id=1114205225977384971)
        await self.member.add_roles(electric_role)
        await interaction.followup.send(f"已經將 {self.member.mention} 加入 {electric_role.mention} 身分組！")
        embed = discord.Embed(title="身分組更新！", description=f"你已加入 {electric_role.name} 身分組。", color=electric_role.color)
        await self.member.send(embed=embed)

    @discord.ui.button(label="管理員(危險！)", style=discord.ButtonStyle.red, emoji="⚠️", row=2)
    async def manager(self, button: discord.ui.Button, interaction: discord.Interaction):
        manager_role = discord.utils.get(self.server_roles, id=1114205838144454807)
        await self.member.add_roles(manager_role)
        await interaction.followup.send(f"已經將 {self.member.mention} 加入 {manager_role.mention} 身分組！")
        embed = discord.Embed(title="身分組更新！", description=f"你已加入 {manager_role.name} 身分組。", color=manager_role.color)
        await self.member.send(embed=embed)

    @discord.ui.button(label="踢出(危險！)", style=discord.ButtonStyle.red, emoji="⏏️", row=2)
    async def kick(self, button: discord.ui.Button, interaction: discord.Interaction):
        embed = discord.Embed(title="審核失敗", description="由於管理員認為你的真實身分與帳號不符，你即將被踢出伺服器。", color=error_color)
        await self.member.send(embed=embed)
        await self.member.kick()
        await interaction.followup.send(f"已經將 {self.member.mention} 踢出伺服器！")


class ConfirmDownload(discord.ui.View):
    def __init__(self, url: str, bit_rate: int = 128):
        super().__init__()
        self.url = url
        self.bit_rate = bit_rate

    @discord.ui.button(style=discord.ButtonStyle.blurple, label="確認下載", emoji="✅")
    async def yes_btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        button.disabled = True
        embed = discord.Embed(
            title="確認下載",
            description="已開始下載，請稍候。",
            color=default_color)
        embed.set_footer(text="下載所需時間依影片長度、網路狀況及影片來源端而定。")
        await interaction.response.edit_message(embed=embed, view=None)
        result = await run_blocking(youtube_start_download, self.url, self.bit_rate)
        if isinstance(result, discord.File):
            try:
                await interaction.edit_original_response(embed=None, file=result)
            except Exception as e:
                if "Request entity too large" in str(e):
                    embed = discord.Embed(title="錯誤", description="檔案過大，無法上傳。", color=error_color)
                    embed.add_field(name="錯誤訊息", value=f"```{e}```", inline=False)
                else:
                    embed = discord.Embed(title="錯誤", description="發生未知錯誤。", color=error_color)
                    embed.add_field(name="錯誤訊息", value=f"```{e}```", inline=False)
                await interaction.edit_original_response(embed=embed)
        elif isinstance(result, discord.Embed):
            await interaction.response.edit_message(embed=result)

    @discord.ui.button(style=discord.ButtonStyle.danger, label="取消下載", emoji="❌")
    async def no_btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        button.disabled = True
        embed = discord.Embed(
            title="取消下載",
            description="已取消下載。",
            color=error_color)
        await interaction.response.edit_message(embed=embed, view=None)


class AgreeTOS(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id

    @discord.ui.button(style=discord.ButtonStyle.blurple, label="同意", emoji="✅")
    async def agree_btn_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        button.disabled = True
        await interaction.response.edit_message(view=None)
        json_assistant.set_agree_TOS_of_anonymous(self.user_id, True)
        embed = discord.Embed(title="成功", description="你已同意使用條款，可以開始使用匿名訊息服務。", color=default_color)
        embed.set_footer(text="如果你想反悔，請使用/anonymous agree_tos指令，並將「同意」改為False即可。")
        await interaction.edit_original_response(embed=embed)


def youtube_start_download(url: str, bit_rate: int) -> discord.File:
    file_name = yt_download.get_id(url)
    mp3_file_name = f"{file_name}_{bit_rate}.mp3"
    mp3_file_path = os.path.join(base_dir, "ytdl", mp3_file_name)
    if os.path.exists(mp3_file_path) or main_dl(url, file_name, mp3_file_name, bit_rate) == "finished":
        return discord.File(mp3_file_path)


async def run_blocking(blocking_func: typing.Callable, *args, **kwargs) -> typing.Any:
    """Runs a blocking function in a non-blocking way"""
    func = functools.partial(blocking_func, *args, **kwargs)
    return await bot.loop.run_in_executor(None, func)


@bot.event
async def on_member_join(member):
    guild_joined = member.guild
    embed = discord.Embed(title="歡迎新成員！", description=f"歡迎{member.mention}加入**{member.guild}**！",
                          color=0x16D863)
    join_date = member.joined_at.astimezone(tz=now_tz).strftime("%Y-%m-%d %H:%M:%S")
    embed.set_footer(text=f"於 {join_date} 加入")
    embed.set_thumbnail(url=member.display_avatar)
    await guild_joined.system_channel.send(embed=embed)
    json_assistant.set_join_date(member.id, join_date)
    new_member = await bot.fetch_user(member.id)
    if guild_joined.id == 857996539262402570:
        embed = discord.Embed(
            title=f"歡迎加入 {member.guild.name} ！",
            description="請到[這裡](https://discord.com/channels/857996539262402570/858373026960637962)查看頻道介紹。",
            color=0x57c2ea)
        await new_member.send(embed=embed)
        embed = discord.Embed(
            title="在開始之前...",
            description="什麼頻道都沒看到嗎？這是因為你**並未被分配身分組**。但是放心，我們會盡快確認你的身分，到時你就能加入我們了！",
            color=0x57c2ea)
        await new_member.send(embed=embed)
        embed = discord.Embed(
            title="取得臨時身分組", description="在取得正式身分組前，請點擊下方按鈕取得臨時身分組。", color=0x57c2ea)
        await new_member.send(embed=embed, view=GetTmpRole())
    elif guild_joined.id == 1114203090950836284:
        embed = discord.Embed(
            title=f"歡迎加入 {member.guild.name} ！",
            description="在正式加入此伺服器前，請告訴我們你的**真名**，以便我們授予你適當的權限！",
            color=0x57c2ea)
        try:
            await new_member.send(embed=embed, view=VerificationModalToView())
        except discord.errors.HTTPException as error:
            if error.code == 50007:
                await guild_joined.system_channel.send(f"{member.mention}，由於你的私人訊息已關閉，無法透過機器人進行快速審核。\n"
                                                       f"請私訊管理員你的**真名**，以便我們授予你適當的身分組！")
            else:
                raise error


@bot.event
async def on_member_remove(member):
    embed = discord.Embed(title="有人離開了我們...", description=f"{member.name} 離開了 **{member.guild}** ...",
                          color=0x095997)
    leave_date = datetime.datetime.now(tz=now_tz).strftime("%Y-%m-%d %H:%M:%S")
    embed.set_footer(text=f"於 {leave_date} 離開")
    await member.guild.system_channel.send(embed=embed)


@bot.event
async def on_application_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(title="指令冷卻中", description=f"這個指令正在冷卻中，請在`{round(error.retry_after)}`秒後再試。",
                              color=error_color)
        await ctx.respond(embed=embed, ephemeral=True)
    elif isinstance(error, commands.NotOwner):
        embed = discord.Embed(title="錯誤", description="你沒有權限使用此指令。", color=error_color)
        await ctx.respond(embed=embed, ephemeral=True)
    else:
        raise error


@bot.event
async def on_ready():
    real_logger.info("機器人準備完成！")
    real_logger.info(f"PING值：{round(bot.latency * 1000)}ms")
    real_logger.info(f"登入身分：{bot.user.name}#{bot.user.discriminator}")
    await set_presence_as_year_process.start()
    # await bot.change_presence(activity=normal_activity, status=discord.Status.online)
    # await check_voice_channel()
    await give_voice_exp.start()


@bot.slash_command(name="help", description="提供指令協助。")
async def help(ctx,
               私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):  # noqa
    embed = discord.Embed(title="指令協助", color=default_color)
    embed.add_field(name="想要知道如何使用本機器人？", value="請參閱在GitHub上的[Wiki]"
                    "(https://github.com/Alllen95Wei/My-Discord-Bot-Slash/wiki/)。")
    await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="about", description="提供關於這隻機器人的資訊。")
async def about(ctx,
                私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):  # noqa
    embed = discord.Embed(title="關於", color=default_color)
    embed.set_thumbnail(url=bot.user.display_avatar)
    embed.add_field(name="程式碼與授權", value="本機器人由<@657519721138094080>維護，使用[Py-cord]"
                                         "(https://github.com/Pycord-Development/pycord)進行開發。\n"
                                         "本機器人的程式碼及檔案皆可在[這裡](https://github.com/Alllen95Wei/My-Discord-Bot-Slash)查看。",
                    inline=True)
    embed.add_field(name="聯絡", value="如果有任何技術問題及建議，請聯絡<@657519721138094080>。", inline=True)
    repo = git.Repo(search_parent_directories=True)
    update_msg = repo.head.reference.commit.message
    raw_sha = repo.head.object.hexsha
    sha = raw_sha[:7]
    embed.add_field(name=f"分支訊息：{sha}", value=update_msg, inline=False)
    year = time.strftime("%Y")
    embed.set_footer(text=f"©Allen Why, {year} | 版本：commit {sha[:7]}")
    await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="ama", description="就是8號球，給你這個問題的隨機回答。")
async def ama(ctx,
              問題: Option(str, "你要問的問題", required=True),  # noqa
              私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):  # noqa
    ans1 = ("g", "s", "b")
    ans_g = ("看起來不錯喔", "肯定的", "我覺得可行", "絕對OK", "是的", "確定", "200 OK", "100 Continue",
             "Just do it")
    ans_s = (
        "現在別問我", "404 Not Found", "你的問題超出宇宙的範圍了", "答案仍在變化", "400 Bad Request",
        "這問題實在沒人答得出來",
        "Answer=A=Ans=答案",
        "最好不要現在告訴你", "300 Multiple Choices", "去問瑪卡巴卡更快",
        "您撥的電話無人接聽，嘟聲後開始計費。", "對不起，您播的號碼是空號，請查明後再撥。")

    ans_b = (
        "不可能", "否定的", "不值得", "等等等等", "No no no", "我拒絕", "我覺得不行耶", "403 Forbidden", "這樣不好")

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
    embed = discord.Embed(title="8號球", description=f"你的問題：{問題}", color=default_color)
    embed.add_field(name="回答", value=f"{ball_result1}\"{ball_result2}\"", inline=False)
    await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="random", description="在指定數字範圍隨機取得一數。")
async def random(ctx,
                 range_min: Option(name="min", description="最小值", required=True, input_type=int),
                 range_max: Option(name="max", description="最大值", required=True, input_type=int),
                 私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):  # noqa
    ans = randint(int(range_min), int(range_max))
    embed = discord.Embed(title="隨機", description=f"數字範圍：{range_min}~{range_max}", color=default_color)
    embed.add_field(name="結果", value=f"`{ans}`", inline=False)
    await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="qrcode", description="將輸入的文字轉為QR Code。")
async def qrcode(ctx,
                 內容: Option(str, "要轉換的文字", required=True),  # noqa
                 私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):  # noqa
    import urllib.parse
    text = urllib.parse.quote(內容)
    url = f"https://chart.apis.google.com/chart?cht=qr&chs=500x500&choe=UTF-8&chld=H|1&chl={text}"
    embed = discord.Embed(title="QR Code", description=f"內容：{內容}", color=default_color)
    embed.set_image(url=url)
    await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="daily", description="每日簽到！")
async def daily(ctx,
                贈與使用者: Option(discord.User, "要贈與每日獎勵的對象", required=False) = None,  # noqa
                私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):  # noqa
    last_claimed_time = json_assistant.get_last_daily_reward_claimed(ctx.author.id)
    if last_claimed_time is None:
        last_claimed_time = 0.0
    last_claimed_time_str = datetime.datetime.fromtimestamp(last_claimed_time, tz=now_tz).strftime("%Y-%m-%d")
    now_time_str = datetime.datetime.fromtimestamp(time.time(), tz=now_tz).strftime("%Y-%m-%d")
    if now_time_str == last_claimed_time_str:
        embed = discord.Embed(title="每日簽到", description=f"你今天已經在<t:{int(last_claimed_time)}:t>簽到過了！",
                              color=error_color)
    else:
        random_reference = randint(1, 200)
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
        if 贈與使用者 and 贈與使用者.id != ctx.author.id:
            receiver = 贈與使用者
            try:
                receiver_embed = discord.Embed(title="🎁收到贈禮！",
                                               description=f"你收到來自{ctx.author.mention}的**`{reward}`點文字經驗值**贈禮！",
                                               color=default_color)
                receiver_embed.add_field(name="回禮", value="你可以在1小時內點擊下方按鈕，即可回送10點文字經驗值給對方作為回禮。",
                                         inline=False)
                await receiver.send(embed=receiver_embed, view=GiftInTurn(ctx.author))
            except discord.errors.Forbidden:
                real_logger.warning(f"無法傳送贈禮通知給 {receiver.name}#{receiver.discriminator}，因為該用戶已關閉私人訊息。")
        else:
            receiver = ctx.author
        json_assistant.add_exp(receiver.id, "text", reward)
        embed = discord.Embed(title="每日簽到",
                              description=f"簽到成功！{receiver.mention}獲得*文字*經驗值`{reward}`點！",
                              color=default_color)
        json_assistant.set_last_daily_reward_claimed(ctx.author.id, time.time())
        json_assistant.add_daily_reward_probability(reward)
        embed.add_field(name="(DEBUG) Random Reference Value", value=f"{random_reference}", inline=False)
        if json_assistant.level_calc(receiver.id, "text"):
            real_logger.info(f"等級提升：{receiver.name} 文字等級"
                             f"達到 {json_assistant.get_level(receiver.id, 'text')} 等")
            lvl_up_embed = discord.Embed(title="等級提升", description=f":tada:恭喜 <@{receiver.id}> *文字*等級升級到 "
                                                                   f"**{json_assistant.get_level(receiver.id, 'text')}"
                                                                   f"** 等！",
                                         color=default_color)
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
        embed.add_field(name=f"{j}點", value=f"{daily_reward_prob_raw_data[str(j)]}次 "
                             f"({round(daily_reward_prob_raw_data[str(j)] / sum_of_rewards * 100, 1)} %)",
                        inline=False)
    await ctx.respond(embed=embed, ephemeral=私人訊息)


user_info = bot.create_group(name="user_info", description="使用者的資訊、經驗值等。")


@user_info.command(name="show", description="顯示使用者的資訊。")
async def show(ctx,
               使用者: Option(discord.Member, "要查詢的使用者", required=False) = None,  # noqa
               私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):  # noqa
    if 使用者 is None:
        使用者 = ctx.author  # noqa
    text_exp = json_assistant.get_exp(使用者.id, "text")
    text_level = json_assistant.get_level(使用者.id, "text")
    voice_exp = json_assistant.get_exp(使用者.id, "voice")
    voice_level = json_assistant.get_level(使用者.id, "voice")
    embed = discord.Embed(title="經驗值", description=f"使用者：{使用者.mention}的經驗值", color=default_color)
    embed.add_field(name="文字等級", value=f"{text_level}", inline=False)
    embed.add_field(name="文字經驗值", value=f"{text_exp}", inline=False)
    embed.add_field(name="語音等級", value=f"{voice_level}", inline=False)
    embed.add_field(name="語音經驗值", value=f"{voice_exp}", inline=False)
    date = None
    if isinstance(使用者, discord.member.Member):
        guild = ctx.guild
        guild_name = guild.name
        date = guild.get_member(使用者.id).joined_at.astimezone(tz=now_tz)
    elif isinstance(使用者, discord.user.User):
        guild_name = "Discord"
        date = 使用者.created_at.astimezone(tz=now_tz)
    date = date.timestamp()
    embed.add_field(name=f"加入 {guild_name} 時間 (UTC+8)", value=f"<t:{int(date)}>", inline=False)
    embed.set_thumbnail(url=使用者.display_avatar)
    embed.set_footer(text="關於經驗值計算系統，請輸入/user_info about")
    await ctx.respond(embed=embed, ephemeral=私人訊息)


@user_info.command(name="require", description="查詢距離下次升等還差多少經驗值。")
async def require(ctx,
                  使用者: Option(discord.Member, "要查詢的使用者", required=False) = None,  # noqa
                  私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):  # noqa
    if 使用者 is None:
        使用者 = ctx.author  # noqa
    text_lvl = json_assistant.get_level(使用者.id, "text")
    text_require = json_assistant.upgrade_exp_needed(使用者.id, "text")
    text_now = json_assistant.get_exp(使用者.id, "text")
    text_percent = (round(text_now / text_require * 1000)) / 10
    voice_lvl = json_assistant.get_level(使用者.id, "voice")
    voice_require = json_assistant.upgrade_exp_needed(使用者.id, "voice")
    voice_now = json_assistant.get_exp(使用者.id, "voice")
    voice_percent = (round(voice_now / voice_require * 1000)) / 10
    embed = discord.Embed(title="經驗值", description=f"使用者：{使用者.mention}距離升級還差...", color=default_color)
    embed.add_field(name=f"文字等級：{text_lvl}",
                    value=f"升級需要`{text_require}`點\n目前：`{text_now}`點 ({text_percent}%)",
                    inline=False)
    embed.add_field(name=f"語音等級：{voice_lvl}",
                    value=f"升級需要`{voice_require}`點\n目前：`{voice_now}`點 ({voice_percent}%)",
                    inline=False)
    embed.set_footer(text="關於經驗值計算系統，請輸入/user_info about")
    await ctx.respond(embed=embed, ephemeral=私人訊息)


@user_info.command(name="about", description="顯示關於經驗值及等級的計算。")
async def exp_about(ctx):
    embed = discord.Embed(title="關於經驗值及等級", description="訊息將分別以2則訊息傳送！", color=default_color)
    await ctx.respond(embed=embed, ephemeral=True)
    embed = discord.Embed(title="關於經驗值", description="經驗值分為**文字**及**語音**，分別以下列方式計算：",
                          color=default_color)
    embed.add_field(name="文字", value="以訊息長度計算，1字1點。", inline=False)
    embed.add_field(name="語音", value="以待在語音頻道的時長計算，10秒可獲得(1 + 有效人數÷10)點。", inline=False)
    embed.add_field(name="其它限制", value="文字：每則訊息**最多15點**。每個使用者有1則訊息被計入經驗值後，需要**5分鐘冷卻時間**才會繼續計算。\n"
                                       "語音：在同一頻道的**真人成員**必須至少2位。若使用者處於**靜音**或**拒聽**狀態，則**無法獲得經驗值**。",
                    inline=False)
    embed.set_footer(text="有1位使用者使用了指令，因此傳送此訊息。")
    await ctx.channel.send(embed=embed)
    embed = discord.Embed(title="關於等級",
                          description="等級同樣分為**文字**及**語音**。\n根據使用者目前的等級，升級所需的經驗值也有所不同。",
                          color=default_color)
    embed.add_field(name="⚠️注意！", value="每次升級，皆會**__將所需經驗值扣除！__**")
    embed.add_field(name="文字", value="**文字**等級升級所需經驗值的公式為：`80 + 25 × 目前文字等級`", inline=False)
    embed.add_field(name="語音", value="**語音**等級升級所需經驗值的公式為：`50 + 30 × 目前語音等級`", inline=False)
    embed.set_footer(text="有1位使用者使用了指令，因此傳送此訊息。")
    await ctx.channel.send(embed=embed)


@user_info.command(name="show_raw_data", description="顯示使用者的JSON原始資料。")
async def show_raw_data(ctx,
                        使用者: Option(discord.Member, "要查詢的使用者", required=True),  # noqa
                        私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):  # noqa
    raw_data = json_assistant.get_raw_info(使用者.id, False)
    embed = discord.Embed(title="使用者資料", description=f"使用者：{使用者.mention}的原始資料", color=default_color)
    embed.add_field(name="原始資料", value=f"```{raw_data}```", inline=False)
    await ctx.respond(embed=embed, ephemeral=私人訊息)


edit = user_info.create_subgroup(name="edit", description="編輯使用者的資訊。")


@user_info.command(name="edit_exp", description="編輯使用者的經驗值。")
@commands.is_owner()
async def edit_exp(ctx,
                   使用者: Option(discord.Member, "要編輯的使用者", required=True),  # noqa
                   類型: Option(str, "要編輯的經驗值類型", required=True, choices=["text", "voice"]),  # noqa
                   經驗值: Option(int, "要編輯的經驗值數量，若要扣除則輸入負值", required=True),  # noqa
                   私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):  # noqa
    before_exp = json_assistant.get_exp(使用者.id, 類型)
    json_assistant.add_exp(使用者.id, 類型, 經驗值)
    after_exp = json_assistant.get_exp(使用者.id, 類型)
    embed = discord.Embed(title="編輯經驗值", description=f"已編輯{使用者.mention}的**{類型}**經驗值。",
                          color=default_color)
    embed.add_field(name="編輯前", value=before_exp, inline=True)
    if 經驗值 > 0:
        embed.add_field(name="➡️增加", value=f"*{經驗值}*", inline=True)
    else:
        embed.add_field(name="➡️減少", value=f"*{abs(經驗值)}*", inline=True)
    embed.add_field(name="編輯後", value=after_exp, inline=True)
    embed_list = [embed]
    if json_assistant.level_calc(使用者.id, 類型):
        real_logger.info(f"等級提升：{ctx.author.name} 文字等級"
                         f"達到 {json_assistant.get_level(ctx.author.id, 'text')} 等")
        embed = discord.Embed(title="等級提升", description=f":tada:恭喜 <@{ctx.author.id}> *文字*等級升級到 "
                                                        f"**{json_assistant.get_level(ctx.author.id, 'text')}"
                                                        f"** 等！",
                              color=default_color)
        embed.set_thumbnail(url=ctx.author.display_avatar)
        embed_list.append(embed)
    await ctx.respond(embeds=embed_list, ephemeral=私人訊息)


@user_info.command(name="edit_lvl", description="編輯使用者的等級。")
@commands.is_owner()
async def edit_lvl(ctx,
                   使用者: Option(discord.Member, "要編輯的使用者", required=True),  # noqa
                   類型: Option(str, "要編輯的等級類型", required=True, choices=["text", "voice"]),  # noqa
                   等級: Option(int, "要編輯的等級數量，若要扣除則輸入負值", required=True),  # noqa
                   私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):  # noqa
    before_lvl = json_assistant.get_level(使用者.id, 類型)
    json_assistant.add_level(使用者.id, 類型, 等級)
    after_lvl = json_assistant.get_level(使用者.id, 類型)
    embed = discord.Embed(title="編輯經驗值", description=f"已編輯{使用者.mention}的**{類型}**等級。",
                          color=default_color)
    embed.add_field(name="編輯前", value=before_lvl, inline=True)
    if 等級 > 0:
        embed.add_field(name="➡️增加", value=f"*{等級}*", inline=True)
    else:
        embed.add_field(name="➡️減少", value=f"{abs(等級)}", inline=True)
    embed.add_field(name="編輯後", value=after_lvl, inline=True)
    embed.set_footer(text="編輯後等級提升而未跳出通知為正常現象。下次當機器人自動增加經驗值時，即會跳出升級訊息。")
    await ctx.respond(embed=embed, ephemeral=私人訊息)


@user_info.command(name="enable", description="開關經驗值計算功能。")
@commands.is_owner()
async def enable(ctx,
                 啟用: Option(bool, "是否啟用經驗值計算功能", required=False) = None,  # noqa
                 私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):  # noqa: PEP 3131
    global exp_enabled
    if 啟用 is None:
        embed = discord.Embed(title="經驗值計算狀態", description=str(exp_enabled), color=default_color)
    else:
        exp_enabled = 啟用
        if 啟用:
            embed = discord.Embed(title="經驗值計算功能已啟用。", color=default_color)
            await bot.change_presence(activity=normal_activity, status=discord.Status.online)
        else:
            embed = discord.Embed(title="經驗值計算功能已停用。", color=default_color)
            await bot.change_presence(activity=normal_activity, status=discord.Status.do_not_disturb)
    await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="ytdl", description="將YouTube影片下載為mp3。由於Discord有"
                                            "檔案大小限制，因此有時可能會失敗。")
async def ytdl(ctx,
               連結: Option(str, "欲下載的YouTube影片網址", required=True),  # noqa: PEP 3131
               位元率: Option(int, description="下載後，轉換為MP3時所使用的位元率，會影響檔案的大小與品質",  # noqa: PEP 3131
                             choices=[96, 128, 160, 192, 256, 320], required=False) = 128):
    await ctx.defer()
    length = yt_download.get_length(連結)
    if length > 512:
        embed = discord.Embed(title="影片長度過長",
                              description=f"影片長度(`{length}`秒)超過512秒，下載後可能無法成功上傳。是否仍要嘗試下載？",
                              color=error_color)
        confirm_download = ConfirmDownload(url=連結, bit_rate=位元率)
        await ctx.respond(embed=embed, view=confirm_download)
    else:
        embed = discord.Embed(title="確認下載",
                              description="已開始下載，請稍候。",
                              color=default_color)
        embed.set_footer(text="下載所需時間依影片長度、網路狀況及影片來源端而定。")
        start_dl_message = await ctx.respond(embed=embed)
        try:
            await start_dl_message.edit(embed=None, file=await run_blocking(youtube_start_download, 連結, 位元率))
        except Exception as e:
            if "Request entity too large" in str(e):
                embed = discord.Embed(title="錯誤", description="檔案過大，無法上傳。", color=error_color)
                embed.add_field(name="是否調整過位元率？", value="如果你選擇了其他位元率，可能會導致檔案過大。請試著降低位元率。", inline=False)
                embed.add_field(name="錯誤訊息", value=f"```{e}```", inline=False)
            else:
                embed = discord.Embed(title="錯誤", description="發生未知錯誤。", color=error_color)
                embed.add_field(name="錯誤訊息", value=f"```{e}```", inline=False)
            await start_dl_message.edit(embed=embed)


@bot.slash_command(name="cleanytdl", description="清除ytdl的下載資料夾。")
@commands.is_owner()
async def cleanytdl(ctx,
                    私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):  # noqa
    await ctx.defer()
    ytdl_folder = os.path.join(base_dir, "ytdl")
    file_count, folder_size = 0, 0
    for f in os.listdir(ytdl_folder):
        file_count += 1
        folder_size += os.path.getsize(os.path.join(ytdl_folder, f))
        os.remove(os.path.join(ytdl_folder, f))
    embed = discord.Embed(title="清除ytdl的下載資料夾", description="已清除ytdl的下載資料夾。", color=default_color)
    # turn folder_size into human-readable format, MB
    folder_size = round(folder_size / 1024 / 1024, 2)
    embed.add_field(name="清除的檔案數量", value=f"{file_count} 個", inline=False)
    embed.add_field(name="清除的檔案大小", value=f"{folder_size} MB", inline=False)
    await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="rc",
                   description="重新連接至語音頻道。可指定頻道，否則將自動檢測音樂機器人及Allen Why在哪個頻道並加入。")
async def rc(ctx,
             頻道: Option(discord.VoiceChannel, "指定要加入的頻道", required=False),  # noqa: PEP 3131
             私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):  # noqa: PEP 3131
    if 頻道 is None:
        msg = await check_voice_channel()
        if isinstance(msg, int):
            embed = discord.Embed(title="已加入頻道", description=f"已經自動加入了 <#{msg}>！", color=default_color)
        elif isinstance(msg, str):
            embed = discord.Embed(title="錯誤", description=f"發生錯誤：`{msg}`", color=error_color)
        elif msg is None:
            embed = discord.Embed(title="錯誤",
                                  description="找不到<@885723595626676264>及<@657519721138094080>在哪個頻道。",
                                  color=error_color)
        else:
            embed = discord.Embed(title="錯誤", description="發生未知錯誤。", color=error_color)
    else:
        try:
            await 頻道.guild.change_voice_state(channel=頻道)
            embed = discord.Embed(title="已加入頻道", description=f"已經加入了 <#{頻道.id}>！", color=default_color)
        except Exception as e:
            embed = discord.Embed(title="錯誤", description=f"發生錯誤：`{e}`", color=error_color)
    await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="dc", description="從目前的語音頻道中斷連接。")
async def dc(ctx,
             私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):  # noqa: PEP 3131
    try:
        await ctx.guild.change_voice_state(channel=None)
        embed = discord.Embed(title="已斷開連接", description="已經從語音頻道中斷連接。", color=default_color)
    except Exception as e:
        if str(e) == "'NoneType' object has no attribute 'disconnect'":
            embed = discord.Embed(title="錯誤", description="目前沒有連接到任何語音頻道。", color=error_color)
        else:
            embed = discord.Embed(title="錯誤", description=f"發生錯誤：`{e}`", color=error_color)
    await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="dps", description="查詢伺服器電腦的CPU及記憶體使用率。")
async def dps(ctx,
              私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):  # noqa: PEP 3131
    embed = discord.Embed(title="伺服器電腦資訊", color=default_color)
    embed.add_field(name="CPU使用率", value=f"{detect_pc_status.get_cpu_usage()}%")
    embed.add_field(name="記憶體使用率", value=f"{detect_pc_status.get_ram_usage_detail()}")
    await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="ping", description="查詢機器人PING值(ms)。")
async def ping(ctx,
               私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):  # noqa: PEP 3131
    embed = discord.Embed(title="PONG!✨", color=default_color)
    embed.add_field(name="PING值", value=f"`{round(bot.latency * 1000)}` ms")
    await ctx.respond(embed=embed, ephemeral=私人訊息)


anonymous = bot.create_group(name="anonymous", description="匿名訊息系統")
identity_choices = ["貓", "狗", "天竺鼠", "綠鬣蜥", "駱駝", "樹懶", "狐狸", "鯊魚", "熊", "狼", "獅子", "熊貓", "狐猴",
                    "猴子", "火星人", "機器人"]


@anonymous.command(name="tos", description="查看匿名訊息服務的使用條款。")
async def TOS(ctx):
    real_logger.anonymous(f"{ctx.author} 查看了匿名訊息服務的使用條款。")
    embed = discord.Embed(title="關於匿名訊息服務", description="在你使用匿名訊息系統前，我們想先提醒你一些關於匿名訊息系統的事情。"
                                                        "**請務必詳細閱讀以下內容**，以避免你的權利受到侵害！", color=default_color)
    embed.add_field(name="使用規定", value="1. 你的匿名訊息不得帶有令人感到不適的內容。我們有權封鎖你的匿名訊息系統使用權。\n"
                                       "2. 為了避免惡意事件發生，每個`/anonymous`相關的指令操作**皆會被記錄在機器人的紀錄檔中**。"
                                       "但是請放心，除非有特殊事件發生，否則管理員不會查詢紀錄檔。\n"
                                       "3. 如果還有任何問題，皆以<@657519721138094080>為準。歡迎詢問任何相關問題！", inline=False)
    embed.add_field(name="如何同意此使用條款？", value="直接點擊下方的「✅同意」按鈕，以同意此使用條款。\n"
                                             "在同意此條款後，你便能開始使用匿名訊息服務。", inline=False)
    embed.set_footer(text="此使用條款有可能隨著機器人的更新而有所變動。因此，你有可能會不定期被導向到這個地方。")
    await ctx.respond(embed=embed, view=AgreeTOS(ctx.author.id), ephemeral=True)


@anonymous.command(name="agree_tos", description="同意匿名訊息服務的使用條款。")
async def agree_TOS(ctx,
                    同意: Option(bool, "是否同意匿名訊息服務的使用條款", required=True)):  # noqa: PEP 3131
    if 同意 is True:
        json_assistant.set_agree_TOS_of_anonymous(ctx.author.id, True)
        real_logger.anonymous(f"{ctx.author} 同意匿名訊息服務的使用條款。")
        embed = discord.Embed(title="成功", description="你已同意匿名訊息服務的使用條款。", color=default_color)
        embed.set_footer(text="如果你想反悔，一樣使用此指令，但將「同意」改為False即可。")
        await ctx.respond(embed=embed, ephemeral=True)
    elif 同意 is False:
        json_assistant.set_agree_TOS_of_anonymous(ctx.author.id, False)
        real_logger.anonymous(f"{ctx.author} 不同意匿名訊息服務的使用條款。")
        embed = discord.Embed(title="成功", description="你已不同意匿名訊息服務的使用條款。\n"
                                                      "注意：你將無法使用匿名訊息系統！", color=default_color)
        embed.set_footer(text="如果你想同意此條款，一樣使用此指令，但將「同意」改為True即可。")
        await ctx.respond(embed=embed, ephemeral=True)


@anonymous.command(name="register", description="建立新的匿名身分。")
async def register(ctx,
                   身分: Option(str, choices=identity_choices, description="選擇想要的動物身分", required=True)):  # noqa: PEP 3131
    try:
        user_identity = json_assistant.get_anonymous_identity(ctx.author.id)
        embed = discord.Embed(title="錯誤", description="你已建立過匿名身分，無法再建立其他匿名身分。", color=error_color)
        embed.add_field(name="你目前的匿名身分", value=f"{user_identity[0]} #{user_identity[1]}")
        await ctx.respond(embed=embed, ephemeral=True)
    except KeyError:
        if json_assistant.get_agree_TOS_of_anonymous(ctx.author.id) is False:
            await TOS(ctx)
        else:
            new_identity_id = ""
            for i in range(4):
                new_identity_id += str(randint(0, 9))
            new_identity = [身分, new_identity_id]
            json_assistant.set_anonymous_identity(ctx.author.id, new_identity)
            embed = discord.Embed(title="建立身分成功！", description="你的匿名身分已建立成功！", color=default_color)
            embed.add_field(name="你的身分", value=f"{身分} #{new_identity_id}", inline=False)
            real_logger.anonymous(f"{ctx.author} 建立了匿名身分 {身分} #{new_identity_id}。")
            await ctx.respond(embed=embed, ephemeral=True)


@anonymous.command(name="show", description="顯示你的匿名身分。")
async def show_anonymous_identity(ctx):
    if json_assistant.get_agree_TOS_of_anonymous(ctx.author.id) is False:
        await TOS(ctx)
    else:
        try:
            user_identity = json_assistant.get_anonymous_identity(ctx.author.id)
            real_logger.anonymous(f"{ctx.author} 查看了自己的匿名身分。")
            embed = discord.Embed(title="你的匿名身分", color=default_color)
            embed.add_field(name="身分", value=user_identity[0])
            embed.add_field(name="編號", value=user_identity[1])
        except KeyError:
            embed = discord.Embed(title="錯誤", description="你尚未建立匿名身分，請先建立匿名身分。", color=error_color)
        await ctx.respond(embed=embed, ephemeral=True)


@anonymous.command(name="send", description="透過匿名身分傳送訊息。")
async def send_anonymous_msg(ctx,
                             對象: Option(discord.User, "欲傳送匿名訊息的對象", required=True),  # noqa: PEP 3131
                             訊息: Option(str, "想傳送的訊息內容", required=True)):  # noqa: PEP 3131
    if json_assistant.get_agree_TOS_of_anonymous(ctx.author.id) is False:
        await TOS(ctx)
    else:
        try:
            user_identity = json_assistant.get_anonymous_identity(ctx.author.id)
            last_msg_sent_time = json_assistant.get_anonymous_last_msg_sent_time(ctx.author.id)
        except KeyError:
            embed = discord.Embed(title="錯誤", description="你尚未建立匿名身分，請先建立匿名身分。", color=error_color)
            await ctx.respond(embed=embed, ephemeral=True)
            return
        time_delta = time.time() - last_msg_sent_time
        if time_delta < 60:
            embed = discord.Embed(title="錯誤",
                                  description=f"你必須等待`{round(60 - time_delta)}`秒才能再次傳送匿名訊息。",
                                  color=error_color)
        elif not json_assistant.get_allow_anonymous(對象.id):
            embed = discord.Embed(title="錯誤", description="對方不允許接收匿名訊息。", color=error_color)
        else:
            try:
                user_identity_str = f"{user_identity[0]} #{user_identity[1]}"
                msg_embed = discord.Embed(title="匿名訊息", description=f"**{user_identity_str}** 傳送了匿名訊息給你。",
                                          color=default_color)
                msg_embed.add_field(name="訊息內容", value=訊息)
                msg_embed.set_footer(text="如果不想收到匿名訊息，可以使用/anonymous allow指令來調整接受與否。")
                await 對象.send(embed=msg_embed)
                real_logger.anonymous(f"{user_identity_str} 傳送了匿名訊息給 {對象.name}。")
                real_logger.anonymous(f"訊息內容：{訊息}")
                json_assistant.set_anonymous_last_msg_sent_time(ctx.author.id, time.time())
                embed = discord.Embed(title="傳送成功！", description="匿名訊息已傳送成功！", color=default_color)
            except discord.errors.HTTPException as e:
                if "Cannot send messages to this user" in str(e):
                    embed = discord.Embed(title="錯誤", description="對方不允許陌生人傳送訊息。", color=error_color)
                elif "Must be 1024 or fewer in length" in str(e):
                    embed = discord.Embed(title="錯誤", description="訊息內容過長。", color=error_color)
                else:
                    embed = discord.Embed(title="錯誤", description="發生未知錯誤。", color=error_color)
                    embed.add_field(name="錯誤訊息", value=str(e))
        await ctx.respond(embed=embed, ephemeral=True)


@anonymous.command(name="allow", description="允許或拒絕接收匿名訊息。")
async def allow_anonymous_msg(ctx,
                              允許: Option(bool, "是否允許接收匿名訊息", required=True)):  # noqa: PEP 3131
    if json_assistant.get_agree_TOS_of_anonymous(ctx.author.id) is False:
        await TOS(ctx)
    else:
        try:
            json_assistant.set_allow_anonymous(ctx.author.id, 允許)
        except KeyError:
            embed = discord.Embed(title="錯誤", description="你尚未建立匿名身分，請先建立匿名身分。", color=error_color)
            await ctx.respond(embed=embed, ephemeral=True)
            return
        if 允許:
            real_logger.anonymous(f"{ctx.author} 設定為 允許 接收匿名訊息。")
            embed = discord.Embed(title="設定成功！", description="你已**允許**接收匿名訊息。", color=default_color)
        else:
            real_logger.anonymous(f"{ctx.author} 設定為 拒絕 接收匿名訊息。")
            embed = discord.Embed(title="設定成功！", description="你已**拒絕**接收匿名訊息。", color=default_color)
        await ctx.respond(embed=embed, ephemeral=True)


@anonymous.command(name="cancel_all_tos", description="取消所有使用者對服務條款的回應。")
@commands.is_owner()
async def cancel_all_tos(ctx):
    all_anonymous_users = json_assistant.get_anonymous_raw_data().keys()
    for i in all_anonymous_users:
        json_assistant.set_agree_TOS_of_anonymous(i, False)
    real_logger.anonymous(f"{ctx.author} 取消了所有使用者對服務條款的回應。")
    embed = discord.Embed(title="成功", description="所有使用者對服務條款的回應已被取消。", color=default_color)
    await ctx.respond(embed=embed, ephemeral=True)


record = bot.create_group(name="record", description="錄音功能")
connections = {}


@record.command(name="start", description="開始錄音語音頻道。")
async def start_record(ctx):
    try:
        await ctx.defer()
        if ctx.author.voice is None:
            embed = discord.Embed(title="錯誤", description="你必須先加入語音頻道才能使用此指令。", color=error_color)
            await ctx.respond(embed=embed, ephemeral=True)
            return
        else:
            vc = await ctx.author.voice.channel.connect()
            connections.update({ctx.guild.id: vc})
            vc.start_recording(discord.sinks.MP3Sink(), record_finished, ctx.channel)
            embed = discord.Embed(title="開始錄音", description="已開始錄音。", color=default_color)
            embed.add_field(name="頻道", value=f"<#{vc.channel.id}>", inline=False)
            embed.add_field(name="要求錄音的使用者", value=f"{ctx.author.mention}", inline=False)
            recorded_users = "".join([f"<@{user_id}>" for user_id, audio in vc.voice_client.sink.audio_data.items()])
            await ctx.respond(content=recorded_users, embed=embed)
    except discord.errors.ClientException:
        embed = discord.Embed(title="錯誤", description="機器人已經在錄音了。", color=error_color)
        await ctx.respond(embed=embed, ephemeral=True)
    except Exception as e:
        embed = discord.Embed(title="錯誤", description="發生未知錯誤。", color=error_color)
        embed.add_field(name="錯誤訊息", value=f"```{e}```", inline=False)
        await ctx.respond(embed=embed, ephemeral=True)


async def record_finished(sink: discord.sinks, ctx):
    recorded_users = [
        f"<@{user_id}>"
        for user_id, audio in sink.audio_data.items()
    ]
    await sink.vc.disconnect()
    files = [discord.File(audio.file, f"{user_id}.{sink.encoding}") for user_id, audio in sink.audio_data.items()]
    embed = discord.Embed(title="錄音完成", description=f"{ctx.author.mention} 的錄音已完成。", color=default_color)
    embed.add_field(name="頻道", value=f"<#{sink.vc.channel.id}>", inline=False)
    await ctx.channel.send(content=f"{' '.join(recorded_users)}", embed=embed, files=files)


@record.command(name="stop", description="停止錄音。")
async def stop_record(ctx):
    try:
        ctx.voice_client.stop_recording()
        embed = discord.Embed(title="停止錄音", description="已停止錄音。\n"
                                                        "錄音檔將會在**使用「開始錄音」指令的文字頻道**上傳。", color=default_color)
        embed.add_field(name="頻道", value=f"<#{ctx.voice_client.channel.id}>", inline=False)
    except AttributeError:
        embed = discord.Embed(title="錯誤", description="機器人並未在錄音。", color=error_color)
    await ctx.respond(embed=embed, ephemeral=True)

# try:
#     chatbot = ChatGPT.ChatBot()
# except OpenAIAuth.Error:
#     chatbot = None
#     real_logger.error("revChatGPT初始化失敗，停用chat指令。")


# @bot.slash_command(name="chat", description="與ChatGPT對話。")
# @commands.cooldown(1, 10, commands.BucketType.user)
# async def chat(ctx,
#                訊息: Option(str, "想要向ChatGPT傳送的訊息", required=True),  # noqa: PEP 3131
#                私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):  # noqa: PEP 3131
#     if chatbot is None:
#         embed = discord.Embed(title="錯誤", description="ChatGPT初始化時發生錯誤，因此機器人已暫時性停用此指令。", color=error_color)
#         embed.add_field(name="為何會出現此錯誤？", value="可能是：\n"
#                                                 "* 機器人所使用的模組(revChatGPT)發生問題\n"
#                                                 "* ChatGPT端更動\n"
#                                                 "* 其他原因\n"
#                                                 "如果你需要使用ChatGPT，你可以至[官方網站](https://chat.openai.com/)註冊帳戶並使用。",
#                         inline=False)
#     else:
#         global last_chat_used_time
#         if time.time() - last_chat_used_time >= 5:
#             await ctx.defer(ephemeral=私人訊息)
#             last_chat_used_time = time.time()
#             response = await run_blocking(chatbot.chat, 訊息)
#             embed = discord.Embed(title="ChatGPT", description="以下是ChatGPT的回應。", color=default_color)
#             embed.add_field(name="你的訊息", value=訊息, inline=False)
#             embed.add_field(name="ChatGPT的回應", value=response, inline=False)
#             embed.set_footer(text="以上回應皆由ChatGPT產生，與本機器人無關。")
#         else:
#             embed = discord.Embed(title="錯誤", description="短時間內已有人使用此指令。請稍後再試。", color=error_color)
#             embed.add_field(name="為什麼我不能跟其他人一起使用此指令？",
#                             value="由於ChatGPT的時間限制，我們不能在短時間內傳送過多要求，否則可能會無法得到回應。\n"
#                                   "為避免此問題，我們才設計了此機制，以避免使用者的體驗不佳。",
#                             inline=False)
#             私人訊息 = True  # noqa: PEP 3131
#     await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="bullshit", description="唬爛。")
# @commands.cooldown(1, 60, commands.BucketType.user)
async def bullshit_cmd(ctx,
                   關鍵字: Option(str, "想要唬爛的關鍵字", required=True),  # noqa: PEP 3131
                   字數: Option(int, "想要唬爛的字數(最多1000)", required=False) = 200,  # noqa: PEP 3131
                   顯著標示關鍵字: Option(bool, "是否顯著標示關鍵字", required=False) = True,  # noqa: PEP 3131
                   私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):  # noqa: PEP 3131
    await ctx.defer(ephemeral=私人訊息)
    content = ""
    if not 0 < 字數 <= 1000:
        embed = discord.Embed(title="錯誤", description=f"你所指定的字數(`{字數}`字)不在1~1000內。", color=error_color)
    else:
        try:
            result = bullshit(關鍵字, 字數)
            embed = discord.Embed(title="唬爛", description="以下是唬爛的結果。", color=default_color)
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
            embed = discord.Embed(title="錯誤", description=f"發生錯誤：`{e}`", color=error_color)
    await ctx.respond(embed=embed, content=content, ephemeral=私人訊息)


@bot.slash_command(name="restart", description="重啟機器人。")
@commands.is_owner()
async def restart(ctx,
                  私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):  # noqa: PEP 3131
    embed = discord.Embed(title="機器人重啟中", description="機器人正在重啟中。", color=default_color)
    await ctx.respond(embed=embed, ephemeral=私人訊息)
    event = discord.Activity(type=discord.ActivityType.playing, name="重啟中...")
    await bot.change_presence(status=discord.Status.idle, activity=event)
    upd.restart_running_bot(os.getpid(), system())


@bot.slash_command(name="screenshot", description="在機器人伺服器端截圖。")
@commands.is_owner()
async def screenshot(ctx,
                     私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):  # noqa: PEP 3131
    try:
        await ctx.defer()
        # 截圖
        img = ImageGrab.grab()
        img.save("screenshot.png")
        file = discord.File("screenshot.png")
        embed = discord.Embed(title="截圖", color=default_color)
        await ctx.respond(embed=embed, file=file, ephemeral=私人訊息)
    except Exception as e:
        embed = discord.Embed(title="錯誤", description=f"發生錯誤：`{e}`", color=error_color)
        await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="cmd", description="在伺服器端執行指令並傳回結果。")
@commands.is_owner()
async def cmd(ctx,
              指令: Option(str, "要執行的指令", required=True),  # noqa: PEP 3131
              執行模組: Option(str, choices=["subprocess", "os"], description="執行指令的模組",  # noqa: PEP 3131
                           required=False) = "subprocess",
              私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):  # noqa: PEP 3131
    try:
        await ctx.defer(ephemeral=私人訊息)
        command = split(指令)
        if command[0] == "cmd":
            embed = discord.Embed(title="錯誤", description="基於安全原因，你不能執行這個指令。", color=error_color)
            await ctx.respond(embed=embed, ephemeral=私人訊息)
            return
        if 執行模組 == "subprocess":
            result = str(run(command, capture_output=True, text=True).stdout)
        else:
            result = str(os.popen(指令).read())
        if result != "":
            embed = discord.Embed(title="執行結果", description=f"```{result}```", color=default_color)
        else:
            embed = discord.Embed(title="執行結果", description="終端未傳回回應。", color=default_color)
    except WindowsError as e:
        if e.winerror == 2:
            embed = discord.Embed(title="錯誤", description="找不到指令。請嘗試更換執行模組。", color=error_color)
        else:
            embed = discord.Embed(title="錯誤", description=f"發生錯誤：`{e}`", color=error_color)
    except Exception as e:
        embed = discord.Embed(title="錯誤", description=f"發生錯誤：`{e}`", color=error_color)
    try:
        await ctx.respond(embed=embed, ephemeral=私人訊息)
    except discord.errors.HTTPException as HTTPError:
        if "fewer in length" in str(HTTPError):
            txt_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "full_msg.txt")
            with open(txt_file_path, "w") as file:
                file.write(str(result))  # noqa
            await ctx.respond("由於訊息長度過長，因此改以文字檔方式呈現。", file=discord.File(txt_file_path),
                              ephemeral=私人訊息)
            os.remove(txt_file_path)


@bot.slash_command(name="update", description="更新機器人。")
@commands.is_owner()
async def update(ctx,
                 私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):  # noqa: PEP 3131
    embed = discord.Embed(title="更新中", description="更新流程啟動。", color=default_color)
    await ctx.respond(embed=embed, ephemeral=私人訊息)
    event = discord.Activity(type=discord.ActivityType.playing, name="更新中...")
    await bot.change_presence(status=discord.Status.idle, activity=event)
    upd.update(os.getpid(), system())


@bot.slash_command(name="test", description="測試用指令。")
@commands.is_owner()
async def test(ctx):
    await on_member_join(ctx.author)
    await ctx.channel.send("測試成功！", delete_after=5)


@bot.user_command(name="查看經驗值")
async def user_info_show_user(ctx, user: discord.Member):
    await show(ctx, user, 私人訊息=True)


@bot.user_command(name="查看升等仍需經驗值")
async def user_info_require_user(ctx, user: discord.Member):
    await require(ctx, user, 私人訊息=True)


@bot.event
async def on_application_command(ctx):
    real_logger.info(f"{ctx.author} 執行了斜線指令 \"{ctx.command.name}\"")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    msg_in = message.content
    exclude_channel = [1035754607286169631, 1035754607286169631, 891665312028713001]
    if message.channel.id == 891665312028713001:
        if msg_in.startswith("https://www.youtube.com") or msg_in.startswith("https://youtu.be") or \
                msg_in.startswith("https://open.spotify.com"):
            if "&list=" in msg_in:
                msg_in = msg_in[:msg_in.find("&list=")]
                await message.channel.send(f"<@{message.author.id}> 偵測到此連結來自播放清單！已轉換為單一影片連結。")
            ap_cmd = "ap!p " + msg_in
            await message.channel.send(ap_cmd)
            return
    if message.channel.id in exclude_channel:
        return
    if exp_enabled:
        time_delta = time.time() - json_assistant.get_last_active_time(message.author.id)
        if time_delta < 300:
            return
        if "Direct Message" in str(message.channel):
            embed = discord.Embed(title="是不是傳錯人了...？", description="很抱歉，目前本機器人不接受私人訊息。", color=error_color)
            await message.channel.send(embed=embed)
            return
        if not message.author.bot and isinstance(msg_in, str):
            if len(msg_in) <= 15:
                real_logger.info(f"獲得經驗值：{message.author.name} 文字經驗值 +{len(msg_in)} (訊息長度：{len(msg_in)})")
                json_assistant.add_exp(message.author.id, "text", len(msg_in))
            else:
                json_assistant.add_exp(message.author.id, "text", 15)
                real_logger.info(f"獲得經驗值：{message.author.name} 文字經驗值 +15 (訊息長度：{len(msg_in)})")
        json_assistant.set_last_active_time(message.author.id, time.time())
        if json_assistant.level_calc(message.author.id, "text"):
            real_logger.info(f"等級提升：{message.author.name} 文字等級"
                             f"達到 {json_assistant.get_level(message.author.id, 'text')} 等")
            embed = discord.Embed(title="等級提升", description=f":tada:恭喜 <@{message.author.id}> *文字*等級升級到 "
                                                            f"**{json_assistant.get_level(message.author.id, 'text')}"
                                                            f"** 等！",
                                  color=default_color)
            embed.set_thumbnail(url=message.author.display_avatar)
            embed.set_footer(text="關於經驗值計算系統，請輸入/user_info about")
            await message.channel.send(embed=embed, delete_after=5)


bot.run(TOKEN)
