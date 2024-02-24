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
    async def ten_mins_ban(self, ctx, user: discord.Member | discord.User):
        current_time = datetime.datetime.now(tz=now_tz)
        timeout_time = current_time + datetime.timedelta(minutes=10)
        await user.timeout(until=timeout_time, reason=f"{ctx.user} 600他")
        embed = Embed(
            title="他被600了！", description=f"{user.mention}已經被600了w", color=default_color
        )
        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(Misfit(bot, bot.logger))
    bot.logger.info('"Misfit"已被載入。')
