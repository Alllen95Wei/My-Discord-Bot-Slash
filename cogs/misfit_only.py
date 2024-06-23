# coding=utf-8
import datetime

import discord
from discord.ext import commands
from discord import Embed
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

prison = {}


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

    @discord.slash_command(
        name="send_to_jail", description="把某人關進監牢！！！", guild_ids=[1030069819199991838]
    )
    @commands.has_permissions(moderate_members=True)
    async def send_to_jail(
        self,
        ctx,
        target_member: Option(
            discord.Member, name="囚犯", description="誰要被送進監牢？", required=True
        ),
        jail_channel: Option(
            discord.VoiceChannel, name="監牢", description="監牢在哪？", required=True
        ),
    ):
        prison[target_member.id] = jail_channel.id
        embed = Embed(
            title="成功！",
            description=f"已經把{target_member.mention}送進監獄！他應該很快就會離開了...",
            color=default_color,
        )
        embed.add_field(name="監獄地點", value=jail_channel.mention, inline=True)
        try:
            await target_member.move_to(jail_channel, reason="坐牢")
        except discord.HTTPException:
            embed.add_field(
                name="哎呀！看來他尚未連線至任何語音頻道...",
                value="但別擔心，他將會在連線至語音頻道的瞬間**強制入獄**！",
                inline=True,
            )
        await ctx.respond(embed=embed)

    @discord.slash_command(
        name="leave_jail", description="把某人救出監牢", guild_ids=[1030069819199991838]
    )
    @commands.has_permissions(moderate_members=True)
    async def leave_jail(
        self,
        ctx,
        target_member: Option(
            discord.Member, name="囚犯", description="誰要被救出監牢？", required=True
        ),
    ):
        if target_member.id in prison.keys():
            del prison[target_member.id]
            embed = Embed(
                title="成功！",
                description=f"{target_member.mention}，恭喜出獄！",
                color=default_color,
            )
            await ctx.respond(embed=embed)
        else:
            embed = Embed(
                title="錯誤：此使用者不在監獄中",
                description=f"{target_member.mention}好像不在監獄之中...",
                color=error_color,
            )
            await ctx.respond(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if after.channel.guild.id == 1030069819199991838 and member.id in prison.keys():
            if after.channel is not None and after.channel.id != prison[member.id]:
                await member.move_to(
                    channel=self.bot.get_channel(prison[member.id]), reason="坐牢"
                )

    # @commands.Cog.listener()
    # async def on_message(self, message: discord.Message):
    #     if message.author.id == self.bot.user.id:
    #         return
    #     if message.guild.id == 1030069819199991838 or message.channel.id == 891665312028713001:
    #         msg_in = message.content
    #         if (
    #             msg_in.startswith("https://www.youtube.com")
    #             or msg_in.startswith("https://youtu.be")
    #             or msg_in.startswith("https://open.spotify.com")
    #             or msg_in.startswith("https://music.youtube.com")
    #         ):
    #             check_vc_result = await self.check_voice_channel()
    #             if isinstance(check_vc_result, str):
    #                 await message.channel.send(
    #                     "**注意：機器人自動加入語音頻道時失敗。音樂機器人可能會回傳錯誤。**",
    #                     delete_after=5)
    #             if "&list=" in msg_in:
    #                 msg_in = msg_in[: msg_in.find("&list=")]
    #                 await message.reply(
    #                     f"{message.author.mention} 偵測到此連結來自播放清單！已轉換為單一影片連結。",
    #                     delete_after=5,
    #                 )
    #             elif "?list=" in msg_in:
    #                 msg_in = msg_in[: msg_in.find("?list=")]
    #                 await message.reply(
    #                     f"{message.author.mention} 偵測到此連結來自播放清單！已轉換為單一影片連結。",
    #                     delete_after=5,
    #                 )
    #             ap_cmd = "ap!p " + msg_in
    #             await message.channel.send(ap_cmd, delete_after=3)
    #             await message.add_reaction("✅")


def setup(bot):
    bot.add_cog(Misfit(bot, bot.logger))
    bot.logger.info('"Misfit"已被載入。')
