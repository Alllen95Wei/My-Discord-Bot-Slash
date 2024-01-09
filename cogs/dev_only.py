import discord
from discord.ext import commands
from discord import Option
import os
import zoneinfo
from pathlib import Path
from platform import system
from shlex import split
from subprocess import run
import git

import logger
import update as upd


error_color = 0xF1411C
default_color = 0x5FE1EA
now_tz = zoneinfo.ZoneInfo("Asia/Taipei")
base_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = str(Path(__file__).parent.parent.absolute())


class DevOnly(commands.Cog):
    def __init__(self, bot: commands.Bot, real_logger: logger.CreateLogger):
        self.bot = bot
        self.real_logger = real_logger

    @discord.slash_command(name="cleanytdl", description="清除ytdl的下載資料夾。")
    @commands.is_owner()
    async def cleanytdl(self, ctx,
                        私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):  # noqa
        await ctx.defer()
        ytdl_folder = os.path.join(parent_dir, "ytdl")
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

    @discord.slash_command(name="cmd", description="在伺服器端執行指令並傳回結果。")
    @commands.is_owner()
    async def cmd(self, ctx,
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
        except FileNotFoundError:
            embed = discord.Embed(title="錯誤", description="找不到指令。請嘗試更換執行模組。", color=error_color)
        except Exception as e:
            embed = discord.Embed(title="錯誤", description=f"發生錯誤：`{e}`", color=error_color)
        try:
            await ctx.respond(embed=embed, ephemeral=私人訊息)
        except discord.errors.HTTPException as HTTPError:
            if "fewer in length" in str(HTTPError):
                txt_file_path = os.path.join(parent_dir, "full_msg.txt")
                with open(txt_file_path, "w") as file:
                    file.write(str(result))  # noqa
                await ctx.respond("由於訊息長度過長，因此改以文字檔方式呈現。", file=discord.File(txt_file_path),
                                  ephemeral=私人訊息)
                os.remove(txt_file_path)

    @discord.slash_command(name="restart", description="重啟機器人。")
    @commands.is_owner()
    async def restart(self, ctx,
                      私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):  # noqa: PEP 3131
        embed = discord.Embed(title="機器人重啟中", description="機器人正在重啟中。", color=default_color)
        await ctx.respond(embed=embed, ephemeral=私人訊息)
        event = discord.Activity(type=discord.ActivityType.playing, name="重啟中...")
        await self.bot.change_presence(status=discord.Status.idle, activity=event)
        upd.restart_running_bot(os.getpid(), system())

    @discord.slash_command(name="update", description="更新機器人。")
    @commands.is_owner()
    async def update(self, ctx,
                     私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):  # noqa: PEP 3131
        embed = discord.Embed(title="更新中", description="更新流程啟動。", color=default_color)
        await ctx.respond(embed=embed, ephemeral=私人訊息)
        repo = git.Repo(search_parent_directories=True)
        old_commit = repo.head.object.hexsha[:7]
        # event = discord.Activity(type=discord.ActivityType.playing, name="更新中...")
        # await self.bot.change_presence(status=discord.Status.idle, activity=event)
        # upd.update(os.getpid(), system())
        upd.get_update_files()
        new_commit = repo.head.object.hexsha[:7]
        embed = discord.Embed(title="更新資訊", description=f"`{old_commit}` ➡️ `{new_commit}`", color=default_color)
        await ctx.respond(embed=embed)

    # @discord.slash_command(name="nothing", description="This command does nothing.")
    # @commands.is_owner()
    # async def nth(self, ctx):
    #     await ctx.respond(content="Nothing happened.", ephemeral=True)

    @discord.slash_command(name="reload", description="重新載入所有extension以套用最新變更。(請先使用「/update」)")
    @commands.is_owner()
    async def reload(self, ctx):
        extension_list = list(self.bot.extensions)
        response_context = "已經重新載入以下extension：\n"
        embed = discord.Embed(title="重新載入", color=0x5FE1EA)
        for extension in extension_list:
            self.bot.reload_extension(extension)
            response_context += extension + "\n"
        embed.description = response_context
        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(DevOnly(bot, bot.logger))
    bot.logger.info("\"DevOnly\"已被載入。")
