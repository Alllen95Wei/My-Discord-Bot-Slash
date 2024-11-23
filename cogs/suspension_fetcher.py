# coding=utf-8
import discord
from discord.ext import commands, tasks
from discord import Embed
import os
import zoneinfo
from pathlib import Path
import pandas as pd

import logger

error_color = 0xF1411C
default_color = 0x5FE1EA
now_tz = zoneinfo.ZoneInfo("Asia/Taipei")
base_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = str(Path(__file__).parent.parent.absolute())


class SuspensionFetcher(commands.Cog):
    def __init__(self, bot: commands.Bot, real_logger: logger.CreateLogger):
        self.bot = bot
        self.real_logger = real_logger
        self.check_TXG.start()

    @tasks.loop(minutes=1)
    async def check_TXG(self):
        self.real_logger.info("開始抓取停班停課資訊")
        with open("TXG_previous_status.txt", "r", encoding="utf-8") as f:
            previous_status = f.read()
        new_status = get_TXG_status()
        if new_status != previous_status:
            self.real_logger.info("資訊更新！")
            with open("TXG_previous_status.txt", "w", encoding="utf-8") as f:
                f.write(new_status)
            embed = Embed(title="臺中市 停課停班狀態變更",
                          description=f"```{previous_status}\n"
                                      "⬇️\n"
                                      f"{new_status}```",
                          color=default_color)
            embed.add_field(name="資料來源", value="https://www.dgpa.gov.tw/typh/daily/nds.html")
            embed.set_footer(text="此功能只花了5分鐘寫出來，會出包很正常。")
            await self.bot.get_channel(858176848747429938).send(content="<@657519721138094080>", embed=embed)
        else:
            self.real_logger.info("資訊無變動")


def setup(bot):
    bot.add_cog(SuspensionFetcher(bot, bot.logger))
    bot.logger.info(f'"{SuspensionFetcher.__name__}"已被載入。')


def get_TXG_status() -> str:
    raw_table = pd.read_html("https://www.dgpa.gov.tw/typh/daily/nds.html", match="是否停止上班上課情形")[0]
    row_count = raw_table.shape[0]
    for r in range(row_count):
        if raw_table[0][r] == "臺中市":
            return raw_table[1][r]


if __name__ == '__main__':
    print(get_TXG_status())
