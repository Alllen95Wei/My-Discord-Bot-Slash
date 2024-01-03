import discord
from discord.ext import commands
from discord import Option
import os
import zoneinfo
from pathlib import Path

import logger


error_color = 0xF1411C
default_color = 0x5FE1EA
now_tz = zoneinfo.ZoneInfo("Asia/Taipei")
base_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = str(Path(__file__).parent.parent.absolute())


class Recorder(commands.Cog):
    def __init__(self, bot: commands.Bot, real_logger: logger.CreateLogger):
        self.bot = bot
        self.real_logger = real_logger
        self.connections = {}

    record = discord.SlashCommandGroup(name="record", description="錄音功能")

    @record.command(name="start", description="開始錄音語音頻道。")
    async def start_record(self, ctx):
        try:
            await ctx.defer()
            if ctx.author.voice is None:
                embed = discord.Embed(title="錯誤", description="你必須先加入語音頻道才能使用此指令。",
                                      color=error_color)
                await ctx.respond(embed=embed, ephemeral=True)
                return
            else:
                vc = await ctx.author.voice.channel.connect()
                self.connections.update({ctx.guild.id: vc})
                vc.start_recording(discord.sinks.MP3Sink(), self.record_finished, ctx.channel)
                embed = discord.Embed(title="開始錄音", description="已開始錄音。", color=default_color)
                embed.add_field(name="頻道", value=f"<#{vc.channel.id}>", inline=False)
                embed.add_field(name="要求錄音的使用者", value=f"{ctx.author.mention}", inline=False)
                recorded_users = "".join(
                    [f"<@{user_id}>" for user_id, audio in vc.voice_client.sink.audio_data.items()])
                await ctx.respond(content=recorded_users, embed=embed)
        except discord.errors.ClientException:
            embed = discord.Embed(title="錯誤", description="機器人已經在錄音了。", color=error_color)
            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(title="錯誤", description="發生未知錯誤。", color=error_color)
            embed.add_field(name="錯誤訊息", value=f"```{e}```", inline=False)
            await ctx.respond(embed=embed, ephemeral=True)

    @staticmethod
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
    async def stop_record(self, ctx):
        try:
            ctx.voice_client.stop_recording()
            embed = discord.Embed(title="停止錄音", description="已停止錄音。\n"
                                                            "錄音檔將會在**使用「開始錄音」指令的文字頻道**上傳。",
                                  color=default_color)
            embed.add_field(name="頻道", value=f"<#{ctx.voice_client.channel.id}>", inline=False)
        except AttributeError:
            embed = discord.Embed(title="錯誤", description="機器人並未在錄音。", color=error_color)
        await ctx.respond(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(Recorder(bot, bot.real_logger))
    bot.logger.info("\"Recorder\"已被載入。")
