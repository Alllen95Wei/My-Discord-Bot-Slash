# coding=utf-8
import discord
from discord.ext import commands
from discord import Option
import os
import time
import zoneinfo
from pathlib import Path

import logger
import json_assistant
from cogs.general import EXCLUDE_CHANNELS

error_color = 0xF1411C
default_color = 0x5FE1EA
now_tz = zoneinfo.ZoneInfo("Asia/Taipei")
base_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = str(Path(__file__).parent.parent.absolute())


class UserInfo(commands.Cog):
    def __init__(self, bot: commands.Bot, real_logger: logger.CreateLogger):
        self.bot = bot
        self.real_logger = real_logger

    user_info = discord.SlashCommandGroup(name="user_info", description="使用者的資訊、經驗值等。")

    @user_info.command(name="show", description="顯示使用者的資訊。")
    async def show(
        self,
        ctx,
        使用者: Option(discord.Member, "要查詢的使用者", required=False) = None,  # noqa
        私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False,  # noqa
    ):
        if 使用者 is None:
            使用者 = ctx.author  # noqa
        user_obj = json_assistant.User(使用者.id)
        text_exp = user_obj.get_exp("text")
        text_level = user_obj.get_level("text")
        voice_exp = user_obj.get_exp("voice")
        voice_level = user_obj.get_level("voice")
        embed = discord.Embed(
            title="經驗值", description=f"使用者：{使用者.mention}的經驗值", color=default_color
        )
        embed.add_field(name="文字等級", value=f"{text_level}", inline=False)
        embed.add_field(name="文字經驗值", value=f"{text_exp}", inline=False)
        embed.add_field(name="語音等級", value=f"{voice_level}", inline=False)
        embed.add_field(name="語音經驗值", value=f"{voice_exp}", inline=False)
        date = None
        if isinstance(使用者, discord.Member):
            guild = ctx.guild
            guild_name = guild.name
            date = guild.get_member(使用者.id).joined_at.astimezone(tz=now_tz)
        elif isinstance(使用者, discord.User):
            guild_name = "Discord"
            date = 使用者.created_at.astimezone(tz=now_tz)
        else:
            guild_name = "Discord"
        date = date.timestamp()
        embed.add_field(
            name=f"加入 {guild_name} 時間 (UTC+8)", value=f"<t:{int(date)}>", inline=False
        )
        embed.set_thumbnail(url=使用者.display_avatar)
        embed.set_footer(text="關於經驗值計算系統，請輸入/user_info about")
        await ctx.respond(embed=embed, ephemeral=私人訊息)

    @discord.user_command(name="查看經驗值")
    async def user_info_show_user(self, ctx, user: discord.Member):
        await self.show(ctx, user, 私人訊息=True)

    @user_info.command(name="require", description="查詢距離下次升等還差多少經驗值。")
    async def require(
        self,
        ctx,
        使用者: Option(discord.Member, "要查詢的使用者", required=False) = None,  # noqa
        私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False,  # noqa
    ):
        if 使用者 is None:
            使用者 = ctx.author  # noqa
        user_obj = json_assistant.User(使用者.id)
        text_lvl = user_obj.get_level("text")
        text_require = user_obj.upgrade_exp_needed("text")
        text_now = user_obj.get_exp("text")
        text_percent = (round(text_now / text_require * 1000)) / 10
        voice_lvl = user_obj.get_level("voice")
        voice_require = user_obj.upgrade_exp_needed("voice")
        voice_now = user_obj.get_exp("voice")
        voice_percent = (round(voice_now / voice_require * 1000)) / 10
        embed = discord.Embed(
            title="經驗值", description=f"使用者：{使用者.mention}距離升級還差...", color=default_color
        )
        embed.add_field(
            name=f"文字等級：{text_lvl}",
            value=f"升級需要`{text_require}`點\n目前：`{text_now}`點 ({text_percent}%)",
            inline=False,
        )
        embed.add_field(
            name=f"語音等級：{voice_lvl}",
            value=f"升級需要`{voice_require}`點\n目前：`{voice_now}`點 ({voice_percent}%)",
            inline=False,
        )
        embed.set_footer(text="關於經驗值計算系統，請輸入/user_info about")
        await ctx.respond(embed=embed, ephemeral=私人訊息)

    @discord.user_command(name="查看升等仍需經驗值")
    async def user_info_require_user(self, ctx, user: discord.Member):
        await self.require(ctx, user, 私人訊息=True)

    @user_info.command(name="about", description="顯示關於經驗值及等級的計算。")
    async def exp_about(self, ctx):
        embed = discord.Embed(
            title="關於經驗值及等級", description="訊息將分別以2則訊息傳送！", color=default_color
        )
        await ctx.respond(embed=embed, ephemeral=True)
        embed = discord.Embed(
            title="關於經驗值",
            description="經驗值分為**文字**及**語音**，分別以下列方式計算：",
            color=default_color,
        )
        embed.add_field(name="文字", value="以訊息長度計算，1字1點。", inline=False)
        embed.add_field(
            name="語音", value="以待在語音頻道的時長計算，10秒可獲得(1 + 有效人數÷10)點。", inline=False
        )
        embed.add_field(
            name="其它限制",
            value="文字：每則訊息**最多15點**。每個使用者有1則訊息被計入經驗值後，需要**5分鐘冷卻時間**才會繼續計算。\n"
            "語音：在同一頻道的**真人成員**必須至少2位。若使用者處於**靜音**或**拒聽**狀態，則**無法獲得經驗值**。",
            inline=False,
        )
        embed.set_footer(text="有1位使用者使用了指令，因此傳送此訊息。")
        await ctx.channel.send(embed=embed)
        embed = discord.Embed(
            title="關於等級",
            description="等級同樣分為**文字**及**語音**。\n根據使用者目前的等級，升級所需的經驗值也有所不同。",
            color=default_color,
        )
        embed.add_field(name="⚠️注意！", value="每次升級，皆會**__將所需經驗值扣除！__**")
        embed.add_field(
            name="文字", value="**文字**等級升級所需經驗值的公式為：`80 + 25 × 目前文字等級`", inline=False
        )
        embed.add_field(
            name="語音", value="**語音**等級升級所需經驗值的公式為：`50 + 30 × 目前語音等級`", inline=False
        )
        embed.set_footer(text="有1位使用者使用了指令，因此傳送此訊息。")
        await ctx.channel.send(embed=embed)

    @user_info.command(name="show_raw_data", description="顯示使用者的JSON原始資料。")
    async def show_raw_data(
        self,
        ctx,
        使用者: Option(discord.Member, "要查詢的使用者", required=True),  # noqa
        私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False,  # noqa
    ):
        raw_data = json_assistant.User(使用者.id).get_raw_info(False)
        embed = discord.Embed(
            title="使用者資料", description=f"使用者：{使用者.mention}的原始資料", color=default_color
        )
        embed.add_field(name="原始資料", value=f"```{raw_data}```", inline=False)
        await ctx.respond(embed=embed, ephemeral=私人訊息)

    @user_info.command(name="edit_exp", description="編輯使用者的經驗值。")
    @commands.is_owner()
    async def edit_exp(
        self,
        ctx,
        使用者: Option(discord.Member, "要編輯的使用者", required=True),  # noqa
        類型: Option(str, "要編輯的經驗值類型", required=True, choices=["text", "voice"]),  # noqa
        經驗值: Option(int, "要編輯的經驗值數量，若要扣除則輸入負值", required=True),  # noqa
        私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False,  # noqa
    ):
        user_obj = json_assistant.User(使用者.id)
        before_exp = user_obj.get_exp(類型)
        user_obj.add_exp(類型, 經驗值)
        after_exp = user_obj.get_exp(類型)
        embed = discord.Embed(
            title="編輯經驗值",
            description=f"已編輯{使用者.mention}的**{類型}**經驗值。",
            color=default_color,
        )
        embed.add_field(name="編輯前", value=before_exp, inline=True)
        if 經驗值 > 0:
            embed.add_field(name="➡️增加", value=f"*{經驗值}*", inline=True)
        else:
            embed.add_field(name="➡️減少", value=f"*{abs(經驗值)}*", inline=True)
        embed.add_field(name="編輯後", value=after_exp, inline=True)
        await ctx.respond(embed=embed, ephemeral=私人訊息)
        if user_obj.level_calc(類型) and user_obj.notify_threshold_reached(類型):
            lvl_type = {"text": "文字", "voice": "語音"}[類型]
            self.real_logger.info(
                f"等級提升：{ctx.author.name} {lvl_type}等級"
                f"達到 {user_obj.get_level(類型)} 等"
            )
            upgrade_embed = discord.Embed(
                title="等級提升",
                description=f":tada:恭喜 <@{ctx.author.id}> *{lvl_type}*等級升級到 "
                f"**{user_obj.get_level(類型)}** 等！",
                color=default_color,
            )
            upgrade_embed.set_thumbnail(url=ctx.author.display_avatar)
            await ctx.respond(embed=upgrade_embed, ephemeral=私人訊息)

    @user_info.command(name="edit_lvl", description="編輯使用者的等級。")
    @commands.is_owner()
    async def edit_lvl(
        self,
        ctx,
        使用者: Option(discord.Member, "要編輯的使用者", required=True),  # noqa
        類型: Option(str, "要編輯的等級類型", required=True, choices=["text", "voice"]),  # noqa
        等級: Option(int, "要編輯的等級數量，若要扣除則輸入負值", required=True),  # noqa
        私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False,  # noqa
    ):
        user_obj = json_assistant.User(使用者.id)
        before_lvl = user_obj.get_level(類型)
        user_obj.add_level(類型, 等級)
        after_lvl = user_obj.get_level(類型)
        embed = discord.Embed(
            title="編輯經驗值",
            description=f"已編輯{使用者.mention}的**{類型}**等級。",
            color=default_color,
        )
        embed.add_field(name="編輯前", value=before_lvl, inline=True)
        if 等級 > 0:
            embed.add_field(name="➡️增加", value=f"*{等級}*", inline=True)
        else:
            embed.add_field(name="➡️減少", value=f"{abs(等級)}", inline=True)
        embed.add_field(name="編輯後", value=after_lvl, inline=True)
        await ctx.respond(embed=embed, ephemeral=私人訊息)
        if user_obj.level_calc(類型) and user_obj.notify_threshold_reached(類型):
            lvl_type = {"text": "文字", "voice": "語音"}[類型]
            self.real_logger.info(
                f"等級提升：{ctx.author.name} {lvl_type}等級"
                f"達到 {user_obj.get_level('類型')} 等"
            )
            upgrade_embed = discord.Embed(
                title="等級提升",
                description=f":tada:恭喜 <@{ctx.author.id}> *{lvl_type}*等級升級到 "
                f"**{user_obj.get_level(類型)}** 等！",
                color=default_color,
            )
            upgrade_embed.set_thumbnail(url=ctx.author.display_avatar)
            await ctx.respond(embed=upgrade_embed, ephemeral=私人訊息)

    @discord.message_command(name="估算訊息經驗值")
    async def calculate_message_exp(self, ctx, message: discord.Message):
        msg_content = message.content
        exp = len(msg_content) if len(msg_content) <= 15 else 15
        embed = discord.Embed(title="估算文字經驗值", color=default_color)
        embed.add_field(name="原訊息內容", value=f"```\n{msg_content}\n```", inline=False)
        embed.add_field(name="訊息長度", value=f"`{len(msg_content)}` 字元", inline=False)
        embed.add_field(name="實領文字經驗值", value=f"`{exp}` 點", inline=True)
        await ctx.respond(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id == self.bot.user.id or message.channel.id in EXCLUDE_CHANNELS:
            return
        if "Direct Message" in str(message.channel):
            embed = discord.Embed(
                title="是不是傳錯人了...？", description="很抱歉，目前本機器人不接受私人訊息。", color=error_color
            )
            await message.channel.send(embed=embed)
            return
        msg_in = message.content
        member_obj = json_assistant.User(message.author.id)
        time_delta = time.time() - member_obj.get_last_active_time()
        if time_delta < 300:
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
    bot.add_cog(UserInfo(bot, bot.logger))
    bot.logger.info('"UserInfo"已被載入。')
