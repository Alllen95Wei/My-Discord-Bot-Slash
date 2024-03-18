# coding=utf-8
import datetime

import discord
from discord.ext import commands
from discord import Option, Embed
import os
import zoneinfo
from pathlib import Path

import logger


error_color = 0xF1411C
default_color = 0x5FE1EA
now_tz = zoneinfo.ZoneInfo("Asia/Taipei")
base_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = str(Path(__file__).parent.parent.absolute())


class Misfit(commands.Cog):
    def __init__(self, bot: commands.Bot, real_logger: logger.CreateLogger):
        self.bot = bot
        self.real_logger = real_logger

    @discord.user_command(name="600他")
    @commands.has_permissions(moderate_members=True)
    async def ten_mins_ban(self, ctx, user: discord.Member | discord.User):
        if ctx.guild.id == 1030069819199991838:
            current_time = datetime.datetime.now(tz=now_tz)
            timeout_time = current_time + datetime.timedelta(minutes=10)
            await user.timeout(until=timeout_time, reason=f"{ctx.user} 600他")
            embed = Embed(
                title="他被600了！",
                description=f"{user.mention}已經被600了w",
                color=default_color,
            )
            await ctx.respond(embed=embed)
        else:
            embed = Embed(
                title="錯誤", description="此指令僅允許在「損友俱樂部」使用！", color=error_color
            )
            await ctx.respond(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id == self.bot.user.id:
            return
        if message.guild.id == 1030069819199991838:
            msg_in = message.content
            if msg_in.startswith("https://www.youtube.com") or msg_in.startswith("https://youtu.be") or \
                    msg_in.startswith("https://open.spotify.com"):
                if "&list=" in msg_in:
                    msg_in = msg_in[:msg_in.find("&list=")]
                    await message.reply(f"{message.author.mention} 偵測到此連結來自播放清單！已轉換為單一影片連結。")
                ap_cmd = "ap!p " + msg_in
                await message.channel.send(ap_cmd)


def setup(bot):
    bot.add_cog(Misfit(bot, bot.logger))
    bot.logger.info('"Misfit"已被載入。')