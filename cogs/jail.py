# coding=utf-8
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

prison: dict[int, discord.VoiceChannel] = {}


class Jail(commands.Cog):
    JAIL_CMDS = discord.SlashCommandGroup(name="jail")

    def __init__(self, bot: commands.Bot, real_logger: logger.CreateLogger):
        self.bot = bot
        self.real_logger = real_logger

    @JAIL_CMDS.command(
        name="lock_in", description="把某人關進監牢！！！", guild_ids=[1030069819199991838]
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
        prison[target_member.id] = jail_channel
        embed = Embed(
            title="成功！",
            description=f"已經把{target_member.mention}送進監獄！他應該很快就會離開了...",
            color=default_color,
        )
        embed.add_field(name="監獄地點", value=jail_channel.mention, inline=False)
        try:
            await target_member.move_to(jail_channel, reason="坐牢")
        except discord.HTTPException:
            embed.add_field(
                name="哎呀！看來他尚未連線至任何語音頻道...",
                value="但別擔心，他將會在連線至語音頻道的瞬間**強制入獄**！",
                inline=False,
            )
        await ctx.respond(embed=embed)

    @JAIL_CMDS.command(
        name="kick", description="把某人移出監牢", guild_ids=[1030069819199991838]
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
        if after.channel is not None and member.id in prison.keys():
            guild_vc_list, guild_vc_id_list = after.channel.guild.voice_channels, []
            for vc in guild_vc_list:
                guild_vc_id_list.append(vc.id)
            if prison[member.id].id in guild_vc_id_list and after.channel.id != prison[member.id].id:
                await member.move_to(channel=prison[member.id], reason="坐牢")


def setup(bot):
    bot.add_cog(Jail(bot, bot.logger))
    bot.logger.info(f'"{Jail.__name__}"已被載入。')
