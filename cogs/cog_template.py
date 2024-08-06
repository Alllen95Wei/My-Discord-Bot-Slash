# coding=utf-8
import discord
from discord.ext import commands
from discord import Embed, Option
import os
import zoneinfo
from pathlib import Path
import time
import datetime

import logger
import json_assistant


error_color = 0xF1411C
default_color = 0x5FE1EA
now_tz = zoneinfo.ZoneInfo("Asia/Taipei")
base_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = str(Path(__file__).parent.parent.absolute())


class Template(commands.Cog):
    def __init__(self, bot: commands.Bot, real_logger: logger.CreateLogger):
        self.bot = bot
        self.real_logger = real_logger


def setup(bot):
    bot.add_cog(Template(bot, bot.logger))
    bot.logger.info(f'"{Template.__name__}"已被載入。')

