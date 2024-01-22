# coding=utf-8
import discord
from discord import ui, Interaction, Embed, Option, InputTextStyle
from discord.ext import commands
import os
import datetime
import time
import zoneinfo
from pathlib import Path

import logger
import json_assistant


error_color = 0xF1411C
default_color = 0x5FE1EA
now_tz = zoneinfo.ZoneInfo("Asia/Taipei")
base_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = str(Path(__file__).parent.parent.absolute())


class Rewards(commands.Cog):
    def __init__(self, bot: commands.Bot, real_logger: logger.CreateLogger):
        self.bot = bot
        self.real_logger = real_logger

    class CreateAward(ui.Modal):
        def __init__(self, outer_instance):
            super().__init__(title="建立兌換代碼")
            self.bot = outer_instance.bot
            self.real_logger = outer_instance.real_logger

            self.add_item(ui.InputText(style=InputTextStyle.short, label="標題", placeholder="輸入代碼標題"))
            self.add_item(ui.InputText(style=InputTextStyle.long, label="說明", required=False,
                                       placeholder="支援markdown"))
            self.add_item(ui.InputText(style=InputTextStyle.short, label="獎勵內容(文字/語音)", value="0/0"))
            self.add_item(ui.InputText(style=InputTextStyle.short, label="限制數量", placeholder="輸入獎勵數量", required=False))
            self.add_item(ui.InputText(style=InputTextStyle.short, label="限制時間 (格式：YYYY/MM/DD HH：MM，24小時制)",
                                       min_length=16, max_length=16, required=False))

        async def callback(self, interaction: Interaction):
            await interaction.response.defer()
            reward_id = json_assistant.RewardData.create_new_reward()
            reward_obj = json_assistant.RewardData(reward_id)
            embed = Embed(title="產生兌換代碼", description=f"成功產生兌換代碼！\n本次的代碼為：`{reward_id}`", color=default_color)
            embed.add_field(name="標題", value=self.children[0].value, inline=False)
            embed.add_field(name="說明", value=self.children[1].value, inline=False) if self.children[1].value else None
            reward_details = self.children[2].value.split("/")
            embed.add_field(name="獎勵內容 (文字)", value=reward_details[0], inline=False)
            embed.add_field(name="獎勵內容 (語音)", value=reward_details[1], inline=False)
            embed.add_field(name="限制數量", value=self.children[3].value, inline=False) if self.children[4].value else None
            reward_obj.set_title(self.children[0].value)
            reward_obj.set_description(self.children[1].value) if self.children[1].value else None
            reward_obj.set_reward("text", int(reward_details[0]))
            reward_obj.set_reward("voice", int(reward_details[1]))
            reward_obj.set_amount(int(self.children[3].value)) if self.children[3].value else None
            if self.children[4].value:
                try:
                    unix_end_time = datetime.datetime.timestamp(
                        datetime.datetime.strptime(self.children[4].value, "%Y/%m/%d %H：%M").replace(tzinfo=now_tz))
                    if unix_end_time < time.time():
                        embed = discord.Embed(title="錯誤",
                                              description=f"輸入的時間(<t:{int(unix_end_time)}:F>)已經過去！請重新輸入。",
                                              color=error_color)
                        reward_obj.delete()
                        await interaction.followup.send(embed=embed, ephemeral=True)
                        return
                    else:
                        reward_obj.set_time_limit(int(unix_end_time))
                        embed.add_field(name="領取截止時間", value=f"<t:{int(unix_end_time)}:F>", inline=False)
                except ValueError:
                    embed = discord.Embed(title="錯誤",
                                          description=f"輸入的時間(`{self.children[2].value}`)格式錯誤！請重新輸入。",
                                          color=error_color)
                    reward_obj.delete()
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
            await interaction.followup.send(embed=embed, ephemeral=True)

    class RedeemConfirmation(ui.View):
        def __init__(self, outer_instance, reward_id):
            super().__init__(timeout=None)
            self.bot = outer_instance.bot
            self.real_logger = outer_instance.real_logger
            self.reward_id = reward_id

        @ui.button(label="確認兌換", style=discord.ButtonStyle.green)
        async def redeem(self, button: ui.Button, interaction: Interaction):
            await interaction.response.defer()
            reward_obj = json_assistant.RewardData(self.reward_id)
            receiver = json_assistant.User(interaction.user.id)
            receiver.add_exp("text", reward_obj.get_rewards()["text"])
            receiver.add_exp("voice", reward_obj.get_rewards()["voice"])
            reward_obj.add_claimed_user(interaction.user.id)
            self.real_logger.info(f"{interaction.user} 領取了代碼 {self.reward_id} 的獎勵。")
            embed = Embed(title="兌換成功", description=f"你已成功兌換代碼`{self.reward_id}`！", color=default_color)
            embed.add_field(name="文字經驗值", value=reward_obj.get_rewards()["text"], inline=False)
            embed.add_field(name="語音經驗值", value=reward_obj.get_rewards()["voice"], inline=False)
            button.disabled = True
            await interaction.edit_original_response(embed=embed, view=self)

    reward = discord.SlashCommandGroup(name="reward", description="與兌換代碼相關的指令。")

    @reward.command(name="create", description="(開發者限定)建立新的兌換代碼。")
    @commands.is_owner()
    async def create(self, ctx):
        await ctx.send_modal(self.CreateAward(self))

    @reward.command(name="redeem", description="兌換代碼。")
    async def redeem(self, ctx,
                     代碼: Option(str, "輸入欲兌換的代碼", min_length=8, max_length=8)):  # noqa
        btn = None
        if 代碼 in json_assistant.RewardData.get_all_reward_id():
            reward_obj = json_assistant.RewardData(代碼)
            if reward_obj.get_time_limit() < time.time():
                embed = Embed(title="錯誤：代碼過期", description=f"你輸入的代碼`{代碼}`已經過期。", color=error_color)
            elif reward_obj.get_amount() and (len(reward_obj.get_claimed_users()) >= reward_obj.get_amount()):
                embed = Embed(title="錯誤：兌換完畢", description=f"你輸入的代碼`{代碼}`已經兌換完畢。", color=error_color)
            elif ctx.author.id in reward_obj.get_claimed_users():
                embed = Embed(title="錯誤：已兌換", description=f"你已兌換過代碼`{代碼}`。", color=error_color)
            else:
                embed = Embed(title="兌換代碼", description=f"代碼`{代碼}`的詳細資訊：", color=default_color)
                embed.add_field(name="標題", value=reward_obj.get_title(), inline=False)
                embed.add_field(name="說明", value=reward_obj.get_description(), inline=False) \
                    if reward_obj.get_description() else None
                embed.add_field(name="獎勵內容(文字)", value=str(reward_obj.get_rewards()["text"]), inline=False)
                embed.add_field(name="獎勵內容(語音)", value=str(reward_obj.get_rewards()["voice"]), inline=False)
                btn = self.RedeemConfirmation(self, 代碼)
        else:
            embed = Embed(title="錯誤", description=f"你輸入的代碼`{代碼}`不存在。", color=error_color)
        await ctx.respond(embed=embed, ephemeral=True, view=btn)


def setup(bot):
    bot.add_cog(Rewards(bot, bot.logger))
    bot.logger.info("\"Rewards\"已被載入。")
