# coding=utf-8
import time
import discord
from discord import Option
from discord.ext import commands
from discord.ext import tasks
import os
import zoneinfo
from pathlib import Path
import json
from json.decoder import JSONDecodeError

import logger
import json_assistant


error_color = 0xF1411C
default_color = 0x5FE1EA
now_tz = zoneinfo.ZoneInfo("Asia/Taipei")
base_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = str(Path(__file__).parent.parent.absolute())

backup_dir = os.path.join(parent_dir, "backup")


class Backup(commands.Cog):
    def __init__(self, bot: commands.Bot, real_logger: logger.CreateLogger):
        self.bot = bot
        self.real_logger = real_logger

    @tasks.loop(minutes=30, reconnect=False)
    async def check_user_data(self):
        start_time = time.time()
        self.real_logger.info("開始使用者資料檢查")
        folder = os.path.join(parent_dir, "user_data")
        user_data_list = [i.split(".")[0] for i in os.listdir(folder)]
        user_data_list.sort()
        for user in user_data_list:
            if not user.isnumeric():
                self.real_logger.info("  " + user + " 不是使用者資料，跳過")
                continue
            self.real_logger.info("  檢查使用者：" + user)
            user_obj = json_assistant.User(user)
            try:
                raw_data = user_obj.get_raw_info(False)
                if raw_data == "":
                    self.real_logger.info("    原始資料檢查：發現錯誤")
                    self.real_logger.info("    開始還原程序...")
                    self.restore_data(user)
                    continue
                else:
                    self.real_logger.debug("    原始資料檢查：通過")
                user_obj.get_level("voice")
                self.real_logger.debug("    語音等級資料檢查：通過")
                user_obj.get_level("text")
                self.real_logger.debug("    文字等級資料檢查：通過")
                user_obj.get_exp("voice")
                self.real_logger.debug("    語音經驗值資料檢查：通過")
                user_obj.get_exp("text")
                self.real_logger.debug("    文字經驗值資料檢查：通過")
                user_obj.get_last_active_time()
                self.real_logger.debug("    最後活躍時間資料檢查：通過")
                user_obj.get_last_daily_reward_claimed()
                self.real_logger.debug("    最後每日獎勵領取時間資料檢查：通過")
                self.real_logger.info("  檢查未發現問題")
            except JSONDecodeError as error:
                self.real_logger.warning("    單項檢查時偵測到錯誤")
                self.real_logger.warning(
                    f"    JSON: 於第 {error.lineno} 行的第 {error.colno} 字元"
                )
                self.real_logger.info("    開始還原程序")
                self.restore_data(user)
                continue
            except Exception as e:
                self.real_logger.warning("    單項檢查時偵測到錯誤")
                self.real_logger.warning(f"    {type(e).__name__}: {str(e)}")
                self.real_logger.info("    開始還原程序")
                self.restore_data(user)
                continue
            self.backup_data(user)
        self.real_logger.info(f"完成使用者資料檢查，耗時 {round(time.time()-start_time, 3)} 秒")

    def backup_data(self, user_id: str):
        self.real_logger.info("  備份使用者資料：" + user_id)
        backup_path = os.path.join(backup_dir, user_id + ".json")
        data = json_assistant.User(user_id).get_raw_info()
        with open(backup_path, "w") as f:
            json.dump(data, f, indent=2)
        self.real_logger.info("  備份完成")

    def restore_data(self, user_id: str):
        self.real_logger.info("  還原使用者資料：" + user_id)
        backup_path = os.path.join(backup_dir, user_id + ".json")
        if os.path.exists(backup_path):
            with open(backup_path, "r") as f:
                data = json.loads(f.read())
            if data == "":
                self.real_logger.info("    使用者沒有備份資料可用，替換為初始化資料")
                data = {
                    "join_date": None,
                    "exp": {"voice": 0, "text": 0},
                    "level": {"voice": 0, "text": 0},
                    "last_active_time": 0,
                    "last_daily_reward_claimed": 0,
                }
            else:
                self.real_logger.info("    成功讀取備份資料")
        else:
            self.real_logger.info("    使用者沒有備份資料可用，替換為初始化資料")
            data = {
                "join_date": None,
                "exp": {"voice": 0, "text": 0},
                "level": {"voice": 0, "text": 0},
                "last_active_time": 0,
                "last_daily_reward_claimed": 0,
            }
        self.real_logger.info("    寫入備份資料中")
        json_assistant.User(user_id).write_raw_info(data)
        self.real_logger.info("  還原完成")

    @commands.Cog.listener()
    async def on_ready(self):
        self.check_user_data.start()

    backup_cmds = discord.SlashCommandGroup(name="recovery")

    @commands.is_owner()
    @backup_cmds.command(name="force_check", description="手動開始檢查資料")
    async def force_check(self, ctx):
        await ctx.defer()
        start_time = time.time()
        await self.check_user_data()
        embed = discord.Embed(
            title="檢查完成",
            description=f"流程耗時 `{round(time.time()-start_time, 3)}` 秒",
            color=default_color,
        )
        await ctx.respond(embed=embed)

    @commands.is_owner()
    @backup_cmds.command(name="force_backup", description="手動開始備份(不檢查資料完整性)")
    async def force_backup(
        self, ctx, user: Option(discord.User, required=False) = None
    ):
        await ctx.defer()
        start_time = time.time()
        if user is None:
            for i in os.listdir(os.path.join(parent_dir, "user_data")):
                file_name = i.split(".")[0]
                if file_name.isnumeric():
                    self.backup_data(file_name)
        else:
            self.backup_data(user.id)
        embed = discord.Embed(
            title="備份完成",
            description=f"流程耗時 `{round(time.time()-start_time, 3)}` 秒",
            color=default_color,
        )
        await ctx.respond(embed=embed)

    @commands.is_owner()
    @backup_cmds.command(name="force_restore", description="手動開始還原(不檢查資料完整性)")
    async def force_restore(self, ctx, user: Option(discord.User, required=True)):
        await ctx.defer()
        start_time = time.time()
        self.restore_data(user.id)
        embed = discord.Embed(
            title="還原完成",
            description=f"流程耗時 `{round(time.time()-start_time, 3)}` 秒",
            color=default_color,
        )
        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(Backup(bot, bot.logger))
    bot.logger.info(f'"{Backup.__name__}"已被載入。')
