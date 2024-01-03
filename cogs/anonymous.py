import discord
from discord.ext import commands
from discord import Option
import os
import zoneinfo
from pathlib import Path
from random import randint
import time

import logger
import json_assistant


error_color = 0xF1411C
default_color = 0x5FE1EA
now_tz = zoneinfo.ZoneInfo("Asia/Taipei")
base_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = str(Path(__file__).parent.parent.absolute())


class Anonymous(commands.Cog):
    def __init__(self, bot: commands.Bot, real_logger: logger.CreateLogger):
        self.bot = bot
        self.real_logger = real_logger

    class AgreeTOS(discord.ui.View):
        def __init__(self, user_id: int):
            super().__init__()
            self.user_id = user_id

        @discord.ui.button(style=discord.ButtonStyle.blurple, label="同意", emoji="✅")
        async def agree_btn_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
            button.disabled = True
            await interaction.response.edit_message(view=None)
            json_assistant.set_agree_TOS_of_anonymous(self.user_id, True)
            embed = discord.Embed(title="成功", description="你已同意使用條款，可以開始使用匿名訊息服務。",
                                  color=default_color)
            embed.set_footer(text="如果你想反悔，請使用/anonymous agree_tos指令，並將「同意」改為False即可。")
            await interaction.edit_original_response(embed=embed)

    anonymous = discord.SlashCommandGroup(name="anonymous", description="匿名訊息系統")
    identity_choices = ("貓", "狗", "天竺鼠", "綠鬣蜥", "駱駝", "樹懶", "狐狸", "鯊魚", "熊", "狼", "獅子", "熊貓",
                        "狐猴", "猴子", "火星人", "機器人")

    @anonymous.command(name="tos", description="查看匿名訊息服務的使用條款。")
    async def TOS(self, ctx):
        self.real_logger.anonymous(f"{ctx.author} 查看了匿名訊息服務的使用條款。")
        embed = discord.Embed(title="關於匿名訊息服務", description="在你使用匿名訊息系統前，我們想先提醒你一些關於匿名訊息系統的事情。"
                                                            "**請務必詳細閱讀以下內容**，以避免你的權利受到侵害！",
                              color=default_color)
        embed.add_field(name="使用規定", value="1. 你的匿名訊息不得帶有令人感到不適的內容。我們有權封鎖你的匿名訊息系統使用權。\n"
                                           "2. 為了避免惡意事件發生，每個`/anonymous`相關的指令操作**皆會被記錄在機器人的紀錄檔中**。"
                                           "但是請放心，除非有特殊事件發生，否則管理員不會查詢紀錄檔。\n"
                                           "3. 如果還有任何問題，皆以<@657519721138094080>為準。歡迎詢問任何相關問題！",
                        inline=False)
        embed.add_field(name="如何同意此使用條款？", value="直接點擊下方的「✅同意」按鈕，以同意此使用條款。\n"
                                                 "在同意此條款後，你便能開始使用匿名訊息服務。", inline=False)
        embed.set_footer(text="此使用條款有可能隨著機器人的更新而有所變動。因此，你有可能會不定期被導向到這個地方。")
        await ctx.respond(embed=embed, view=self.AgreeTOS(ctx.author.id), ephemeral=True)

    @anonymous.command(name="agree_tos", description="同意匿名訊息服務的使用條款。")
    async def agree_TOS(self, ctx,
                        同意: Option(bool, "是否同意匿名訊息服務的使用條款", required=True)):  # noqa: PEP 3131
        if 同意 is True:
            json_assistant.set_agree_TOS_of_anonymous(ctx.author.id, True)
            self.real_logger.anonymous(f"{ctx.author} 同意匿名訊息服務的使用條款。")
            embed = discord.Embed(title="成功", description="你已同意匿名訊息服務的使用條款。", color=default_color)
            embed.set_footer(text="如果你想反悔，一樣使用此指令，但將「同意」改為False即可。")
            await ctx.respond(embed=embed, ephemeral=True)
        elif 同意 is False:
            json_assistant.set_agree_TOS_of_anonymous(ctx.author.id, False)
            self.real_logger.anonymous(f"{ctx.author} 不同意匿名訊息服務的使用條款。")
            embed = discord.Embed(title="成功", description="你已不同意匿名訊息服務的使用條款。\n"
                                                          "注意：你將無法使用匿名訊息系統！", color=default_color)
            embed.set_footer(text="如果你想同意此條款，一樣使用此指令，但將「同意」改為True即可。")
            await ctx.respond(embed=embed, ephemeral=True)

    @anonymous.command(name="register", description="建立新的匿名身分。")
    async def register(self, ctx,
                       身分: Option(str, choices=identity_choices, description="選擇想要的動物身分",  # noqa: PEP 3131
                                    required=True)):
        try:
            user_identity = json_assistant.get_anonymous_identity(ctx.author.id)
            embed = discord.Embed(title="錯誤", description="你已建立過匿名身分，無法再建立其他匿名身分。",
                                  color=error_color)
            embed.add_field(name="你目前的匿名身分", value=f"{user_identity[0]} #{user_identity[1]}")
            await ctx.respond(embed=embed, ephemeral=True)
        except KeyError:
            if json_assistant.get_agree_TOS_of_anonymous(ctx.author.id) is False:
                await self.TOS(ctx)
            else:
                new_identity_id = ""
                for i in range(4):
                    new_identity_id += str(randint(0, 9))
                new_identity = [身分, new_identity_id]
                json_assistant.set_anonymous_identity(ctx.author.id, new_identity)
                embed = discord.Embed(title="建立身分成功！", description="你的匿名身分已建立成功！", color=default_color)
                embed.add_field(name="你的身分", value=f"{身分} #{new_identity_id}", inline=False)
                self.real_logger.anonymous(f"{ctx.author} 建立了匿名身分 {身分} #{new_identity_id}。")
                await ctx.respond(embed=embed, ephemeral=True)

    @anonymous.command(name="show", description="顯示你的匿名身分。")
    async def show_anonymous_identity(self, ctx):
        if json_assistant.get_agree_TOS_of_anonymous(ctx.author.id) is False:
            await self.TOS(ctx)
        else:
            try:
                user_identity = json_assistant.get_anonymous_identity(ctx.author.id)
                self.real_logger.anonymous(f"{ctx.author} 查看了自己的匿名身分。")
                embed = discord.Embed(title="你的匿名身分", color=default_color)
                embed.add_field(name="身分", value=user_identity[0])
                embed.add_field(name="編號", value=user_identity[1])
            except KeyError:
                embed = discord.Embed(title="錯誤", description="你尚未建立匿名身分，請先建立匿名身分。",
                                      color=error_color)
            await ctx.respond(embed=embed, ephemeral=True)

    @anonymous.command(name="send", description="透過匿名身分傳送訊息。")
    async def send_anonymous_msg(self, ctx,
                                 對象: Option(discord.User, "欲傳送匿名訊息的對象", required=True),  # noqa: PEP 3131
                                 訊息: Option(str, "想傳送的訊息內容", required=True)):  # noqa: PEP 3131
        if json_assistant.get_agree_TOS_of_anonymous(ctx.author.id) is False:
            await self.TOS(ctx)
        else:
            try:
                user_identity = json_assistant.get_anonymous_identity(ctx.author.id)
                last_msg_sent_time = json_assistant.get_anonymous_last_msg_sent_time(ctx.author.id)
            except KeyError:
                embed = discord.Embed(title="錯誤", description="你尚未建立匿名身分，請先建立匿名身分。",
                                      color=error_color)
                await ctx.respond(embed=embed, ephemeral=True)
                return
            time_delta = time.time() - last_msg_sent_time
            if time_delta < 60:
                embed = discord.Embed(title="錯誤",
                                      description=f"你必須等待`{round(60 - time_delta)}`秒才能再次傳送匿名訊息。",
                                      color=error_color)
            elif not json_assistant.get_allow_anonymous(對象.id):
                embed = discord.Embed(title="錯誤", description="對方不允許接收匿名訊息。", color=error_color)
            else:
                try:
                    user_identity_str = f"{user_identity[0]} #{user_identity[1]}"
                    msg_embed = discord.Embed(title="匿名訊息",
                                              description=f"**{user_identity_str}** 傳送了匿名訊息給你。",
                                              color=default_color)
                    msg_embed.add_field(name="訊息內容", value=訊息)
                    msg_embed.set_footer(text="如果不想收到匿名訊息，可以使用/anonymous allow指令來調整接受與否。")
                    await 對象.send(embed=msg_embed)
                    self.real_logger.anonymous(f"{user_identity_str} 傳送了匿名訊息給 {對象.name}。")
                    self.real_logger.anonymous(f"訊息內容：{訊息}")
                    json_assistant.set_anonymous_last_msg_sent_time(ctx.author.id, time.time())
                    embed = discord.Embed(title="傳送成功！", description="匿名訊息已傳送成功！", color=default_color)
                except discord.errors.HTTPException as e:
                    if "Cannot send messages to this user" in str(e):
                        embed = discord.Embed(title="錯誤", description="對方不允許陌生人傳送訊息。", color=error_color)
                    elif "Must be 1024 or fewer in length" in str(e):
                        embed = discord.Embed(title="錯誤", description="訊息內容過長。", color=error_color)
                    else:
                        embed = discord.Embed(title="錯誤", description="發生未知錯誤。", color=error_color)
                        embed.add_field(name="錯誤訊息", value=str(e))
            await ctx.respond(embed=embed, ephemeral=True)

    @anonymous.command(name="allow", description="允許或拒絕接收匿名訊息。")
    async def allow_anonymous_msg(self, ctx,
                                  允許: Option(bool, "是否允許接收匿名訊息", required=True)):  # noqa: PEP 3131
        if json_assistant.get_agree_TOS_of_anonymous(ctx.author.id) is False:
            await self.TOS(ctx)
        else:
            try:
                json_assistant.set_allow_anonymous(ctx.author.id, 允許)
            except KeyError:
                embed = discord.Embed(title="錯誤", description="你尚未建立匿名身分，請先建立匿名身分。",
                                      color=error_color)
                await ctx.respond(embed=embed, ephemeral=True)
                return
            if 允許:
                self.real_logger.anonymous(f"{ctx.author} 設定為 允許 接收匿名訊息。")
                embed = discord.Embed(title="設定成功！", description="你已**允許**接收匿名訊息。", color=default_color)
            else:
                self.real_logger.anonymous(f"{ctx.author} 設定為 拒絕 接收匿名訊息。")
                embed = discord.Embed(title="設定成功！", description="你已**拒絕**接收匿名訊息。", color=default_color)
            await ctx.respond(embed=embed, ephemeral=True)

    @anonymous.command(name="cancel_all_tos", description="取消所有使用者對服務條款的回應。")
    @commands.is_owner()
    async def cancel_all_tos(self, ctx):
        all_anonymous_users = json_assistant.get_anonymous_raw_data().keys()
        for i in all_anonymous_users:
            json_assistant.set_agree_TOS_of_anonymous(i, False)
        self.real_logger.anonymous(f"{ctx.author} 取消了所有使用者對服務條款的回應。")
        embed = discord.Embed(title="成功", description="所有使用者對服務條款的回應已被取消。", color=default_color)
        await ctx.respond(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(Anonymous(bot, bot.real_logger))
    bot.logger.info("\"Anonymous\"已被載入。")
