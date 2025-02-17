# coding=utf-8
import discord
from discord.ext import commands
from discord import Embed, ui, ButtonStyle, InputTextStyle, Interaction
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
            appeal_channel: discord.TextChannel = self.outer_instance.bot.get_channel(
                1275005711373570098
            )
            appeal_embed = Embed(
                title="新的申訴",
                description=f"{interaction.user.mention}因為遭到禁言，傳送了申訴。",
                color=default_color,
            )
            appeal_embed.add_field(name="申訴內容", value=self.children[0].value)
            await appeal_channel.send(
                embed=appeal_embed,
                view=Misfit.ReviewView(
                    self.outer_instance,
                    self.outer_instance.bot.get_guild(1030069819199991838).get_member(
                        interaction.user.id
                    ),
                    self.children[0].value,
                ),
            )
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
            member_obj = self.outer_instance.bot.get_guild(
                1030069819199991838
            ).get_member(interaction.user.id)
            if member_obj.timed_out:
                await interaction.response.send_modal(
                    Misfit.AppealWindow(self.outer_instance)
                )
            else:
                embed = Embed(
                    title="錯誤：未被禁言",
                    description="你目前未被禁言，因此無法使用此功能。",
                    color=error_color,
                )
                await interaction.followup.send(embed=embed, ephemeral=True)

    class ReviewView(ui.View):
        def __init__(
            self, outer_instance, timed_out_member: discord.Member, appeal_content: str
        ):
            super().__init__(timeout=None)
            self.outer_instance = outer_instance
            self.timed_out_member = timed_out_member
            self.appeal_content = appeal_content

        @ui.button(label="通過，解除禁言", style=ButtonStyle.green)
        async def allow_callback(self, button, interaction: discord.Interaction):
            await interaction.response.defer()
            if not self.timed_out_member.timed_out:
                embed = Embed(
                    title="錯誤：使用者未被禁言",
                    description=f"{self.timed_out_member.mention} 似乎已被解除禁言。",
                    color=error_color,
                )
            else:
                await self.timed_out_member.timeout(
                    until=None, reason=f"{interaction.user.name} 審核後解除禁言"
                )
                embed = Embed(
                    title="已解除禁言",
                    description=f"{interaction.user.mention} 已解除了 {self.timed_out_member.mention} 的禁言。",
                    color=default_color,
                )
                embed.add_field(name="申訴內容", value=self.appeal_content)
                notify_embed = Embed(
                    title="好消息：申訴通過！",
                    description=f"你的申訴經過 {interaction.user.mention} 的許可，因此你的禁言已解除。",
                    color=default_color,
                )
                await self.timed_out_member.send(embed=notify_embed)
            self.disable_all_items()
            await interaction.edit_original_response(embed=embed)
            await interaction.followup.send(
                view=Misfit.FeedbackView(
                    self.outer_instance, self.timed_out_member, interaction.user
                )
            )

        @ui.button(label="未通過，繼續禁言", style=ButtonStyle.red)
        async def disallow_callback(self, button, interaction: discord.Interaction):
            await interaction.response.defer()
            if not self.timed_out_member.timed_out:
                embed = Embed(
                    title="錯誤：使用者未被禁言",
                    description=f"{self.timed_out_member.mention} 似乎已被解除禁言。",
                    color=error_color,
                )
            else:
                embed = Embed(
                    title="已退回申訴",
                    description=f"{interaction.user.mention} 已退回了 {self.timed_out_member.mention} 的申訴。禁言將繼續。",
                    color=default_color,
                )
                embed.add_field(name="申訴內容", value=self.appeal_content)
                notify_embed = Embed(
                    title="申訴未通過",
                    description=f"你的申訴經過 {interaction.user.mention} 檢查後遭到拒絕，因此你的禁言將繼續。",
                    color=default_color,
                )
                await self.timed_out_member.send(embed=notify_embed)
            self.disable_all_items()
            await interaction.edit_original_response(embed=embed)
            await interaction.followup.send(
                view=Misfit.FeedbackView(
                    self.outer_instance, self.timed_out_member, interaction.user
                )
            )

    class FeedbackView(ui.View):
        def __init__(
            self,
            outer_instance,
            timed_out_member: discord.Member,
            operator: discord.User | discord.Member,
        ):
            super().__init__(disable_on_timeout=True)
            self.outer_instance = outer_instance
            self.timed_out_member = timed_out_member
            self.operator = operator

        @ui.button(label="提供回應", style=ButtonStyle.blurple, emoji="🗨️")
        async def btn_callback(self, button, interaction: discord.Interaction):
            await interaction.response.send_modal(
                Misfit.FeedbackWindow(
                    self.outer_instance,
                    self.timed_out_member,
                    self.operator,
                )
            )

    class FeedbackWindow(ui.Modal):
        def __init__(
            self,
            outer_instance,
            timed_out_member: discord.Member,
            operator: discord.User | discord.Member,
        ):
            super().__init__(title="提供對方回應")
            self.outer_instance = outer_instance
            self.timed_out_member = timed_out_member
            self.operator = operator
            self.add_item(
                ui.InputText(
                    style=InputTextStyle.long,
                    label="回應",
                    max_length=1000,
                    required=True,
                )
            )

        async def callback(self, interaction: Interaction):
            await interaction.response.defer()
            provided_reason = self.children[0].value
            if interaction.user.id != self.operator.id:
                embed = Embed(
                    title="錯誤：非原始操作者",
                    description=f"你不是審核此要求的使用者。{self.operator.mention}才能使用此按鈕。",
                    color=error_color,
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            elif provided_reason is not None:
                embed = Embed(
                    title="已送出回應",
                    description=f"已傳送你的回應給{self.timed_out_member.mention}。",
                    color=default_color,
                )
                embed.add_field(name="你的回應", value=provided_reason)
                await interaction.edit_original_response(embed=embed, view=None)
                response_embed = Embed(
                    title="管理員提供了回應",
                    description=f"{interaction.user.mention}回應了以下內容。",
                    color=default_color,
                )
                response_embed.add_field(name="回應內容", value=provided_reason)
                await self.timed_out_member.send(embed=response_embed)

    @discord.user_command(name="600他")
    @commands.has_permissions(moderate_members=True)
    async def ten_mins_ban(
        self, ctx: discord.ApplicationContext, user: discord.Member | discord.User
    ):
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
        if after.guild.id == 1030069819199991838:
            if not before.timed_out and after.timed_out:  # 遭到禁言
                embed = Embed(
                    title="申訴",
                    description="你似乎遭到禁言。如果需要，你可以點擊下方的按鈕開始申訴。\n你的申訴內容僅會被<@&1123952631207968948>看到。",
                    color=default_color,
                )
                try:
                    await after.send(embed=embed, view=self.AppealView(self))
                except discord.Forbidden or discord.HTTPException:
                    self.real_logger.warning(f"私訊給 {after.name} 時發生錯誤。")
            elif before.timed_out and not after.timed_out:  # 解除禁言
                embed = Embed(
                    title="已解除禁言",
                    description="你的禁言已被解除。",
                    color=default_color,
                )
                try:
                    await after.send(embed=embed)
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
            and (before.channel != after.channel)
            and after.channel.id != 1096730575475318835  # AFK 頻道
            and after.self_mute
            or after.self_deaf
        ):
            msg = member.mention + " ，你目前__**沒有開啟麥克風**__，其他人將無法聽到你的發言。"
            await after.channel.send(msg)


def setup(bot):
    bot.add_cog(Misfit(bot, bot.logger))
    bot.logger.info('"Misfit"已被載入。')
