# coding=utf-8
import discord
from discord.ext import commands
from discord import Embed, ui, ButtonStyle, InputTextStyle
import os
import zoneinfo
from pathlib import Path
import datetime

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

    class AppealWindow(ui.Modal):
        def __init__(self, outer_instance):
            super().__init__(
                ui.InputText(
                    label="申訴內文",
                    style=InputTextStyle.long,
                    required=True,
                ),
                title="提交申訴",
                timeout=None,
            )
            self.outer_instance = outer_instance

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            appeal_channel = self.outer_instance.bot.get_channel(1275005711373570098)
            appeal_embed = Embed(
                title="新的申訴",
                description=f"{interaction.user.mention}因為遭到禁言，傳送了申訴。",
                color=default_color,
            )
            appeal_embed.add_field(name="申訴內容", value=self.children[0].value)
            await appeal_channel.send(embed=appeal_embed)
            embed = Embed(title="已送出申訴", description="已送出你的申訴。", color=default_color)
            appeal_embed.add_field(name="申訴內容", value=self.children[0].value)
            await interaction.edit_original_response(embed=embed, view=None)

    class AppealView(ui.View):
        def __init__(self, outer_instance):
            super().__init__(timeout=None)
            self.outer_instance = outer_instance

        @ui.button(
            label="提交申訴",
            style=ButtonStyle.blurple,
            emoji="🙋‍♂️",
        )
        async def btn_callback(self, button, interaction: discord.Interaction):
            member_obj = self.outer_instance.bot.get_guild(1030069819199991838).get_member(interaction.user.id)
            if member_obj.timed_out:
                await interaction.response.send_modal(Misfit.AppealWindow(self.outer_instance))
            else:
                embed = Embed(
                    title="錯誤：未被禁言",
                    description="你目前未被禁言，因此無法使用此功能。",
                    color=error_color,
                )
                await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.user_command(name="600他")
    @commands.has_permissions(moderate_members=True)
    async def ten_mins_ban(self, ctx: discord.ApplicationContext, user: discord.Member | discord.User):
        if ctx.guild.id == 1030069819199991838:
            current_time = datetime.datetime.now(tz=now_tz)
            timeout_time = current_time + datetime.timedelta(minutes=10)
            await user.timeout(until=timeout_time, reason=f"{ctx.user} 600他")
            embed = Embed(
                title="他被600了！",
                description=f"{user.mention}已經被600了w",
                color=default_color,
            )
            await ctx.respond(embed=embed, ephemeral=True)
        else:
            embed = Embed(
                title="錯誤", description="此指令僅允許在「損友俱樂部」使用！", color=error_color
            )
            await ctx.respond(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if (after.guild.id == 1030069819199991838) and (not before.timed_out and after.timed_out):
            embed = Embed(
                title="申訴",
                description="你似乎遭到禁言。如果需要，你可以點擊下方的按鈕開始申訴。\n你的申訴內容僅會被<@&1123952631207968948>看到。",
                color=default_color,
            )
            try:
                await after.send(embed=embed, view=self.AppealView(self))
            except discord.Forbidden or discord.HTTPException:
                self.real_logger.warning(f"私訊給 {after.name} 時發生錯誤。")

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if (
            (not member.bot)
            and (after.channel is not None)
            and (after.channel.guild.id == 1030069819199991838)  # 損友俱樂部
        ):
            if (before.channel != after.channel) and (
                after.self_mute or after.self_deaf
            ):
                msg = member.mention + " ，你目前__**沒有開啟麥克風**__，其他人將無法聽到你的發言。"
                await after.channel.send(msg, tts=True)


def setup(bot):
    bot.add_cog(Misfit(bot, bot.logger))
    bot.logger.info('"Misfit"已被載入。')
