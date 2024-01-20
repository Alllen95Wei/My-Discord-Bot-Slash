# coding=utf-8
import discord
from discord import ui, Interaction, Embed, SelectOption, Option
from discord.ext import commands
import os
import zoneinfo
from pathlib import Path

import logger
import json_assistant


error_color = 0xF1411C
default_color = 0x5FE1EA
announcement_color = 0x20BA49
now_tz = zoneinfo.ZoneInfo("Asia/Taipei")
base_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = str(Path(__file__).parent.parent.absolute())


class Announcement(commands.Cog):
    def __init__(self, bot: commands.Bot, real_logger: logger.CreateLogger):
        self.bot = bot
        self.real_logger = real_logger

    class CreateAnnouncement(ui.Modal):
        def __init__(self, outer_instance, announcement_type: str):
            super().__init__(title="公告草稿")
            self.announcement_type = announcement_type
            self.bot = outer_instance.bot
            self.real_logger = outer_instance.real_logger

            self.add_item(ui.InputText(style=discord.InputTextStyle.short, label="類型", value=announcement_type))
            self.add_item(ui.InputText(style=discord.InputTextStyle.long, label="公告內文",
                                       placeholder="請輸入公告內容(支援markdown)"))

        async def callback(self, interaction: Interaction):
            await interaction.response.defer()
            title_types = {"一般公告": "📢一般公告",
                           "更新通知": "🔄️更新通知",
                           "緊急公告": "🚨緊急公告",
                           "雜七雜八": "💬雜七雜八"}
            announcement_content = (self.children[1].value +
                                    f"\n\n*\\- {self.bot.get_user(self.bot.owner_id).display_name}*")  # 加上署名
            announcement_embed = Embed(title=title_types[self.announcement_type],
                                       description=announcement_content, color=announcement_color)
            announcement_embed.set_footer(text=f"由於你訂閱了「{self.announcement_type}」類別，因此收到了這則訊息。")
            receiver_data = json_assistant.get_announcement_receivers()
            successful_users, failed_users, unsubscribed_users = "", "", ""
            for receiver in receiver_data:
                receiver_obj = self.bot.get_user(int(receiver))
                if self.announcement_type in receiver_data[receiver]:
                    try:
                        await receiver_obj.send(embed=announcement_embed)
                        successful_users += f"<@{receiver}>\n"
                        self.real_logger.info(f"傳送公告成功：{receiver_obj}")
                    except Exception as e:
                        failed_users += f"<@{receiver}>\n"
                        self.real_logger.info(f"傳送公告失敗：{receiver_obj}({e})")
                else:
                    unsubscribed_users += f"<@{receiver}>\n"
                    self.real_logger.debug(f"未訂閱：{receiver_obj}")
            response_embed = Embed(title="已發布公告！", description="傳送結果如下：", color=default_color)
            response_embed.add_field(name="✅傳送成功", value=successful_users)
            response_embed.add_field(name="❌傳送失敗", value=failed_users)
            response_embed.add_field(name="0️⃣未訂閱", value=unsubscribed_users)
            await interaction.followup.send(embed=response_embed, ephemeral=True)

    class AnnouncementSelection(ui.View):
        choices = [SelectOption(label="❌取消所有訂閱", description="取消所有訂閱(將忽略其它選擇)"),
                   SelectOption(label="📢一般公告", description="不定期提供使用提示、功能介紹！", value="一般公告"),
                   SelectOption(label="🔄️更新通知", description="在新指令、功能發布時，可以獲得及時通知和簡介！", value="更新通知"),
                   SelectOption(label="🚨緊急公告", description="機器人發生重大故障時，立即獲得警示！", value="緊急公告"),
                   SelectOption(label="💬雜七雜八", description="聽一下Allen Why的幹話和...？", value="雜七雜八")]

        def __init__(self, outer_instance):
            super().__init__()
            self.real_logger = outer_instance.real_logger

        @ui.select(placeholder="選擇要訂閱的通知類別(可多選)", min_values=0, max_values=len(choices), options=choices)
        async def select_callback(self, selects, interaction: discord.Interaction):
            await interaction.response.defer()
            embed = Embed(title="變更完成！", description="你將收到以下的通知：\n", color=default_color)
            if len(selects.values) == 0 or "❌取消所有訂閱" in selects.values:
                embed.description = "你將不會收到任何通知。"
                json_assistant.edit_announcement_receiver(interaction.user.id, [])
                self.real_logger.info(f"{interaction.user} 取消訂閱了所有內容。")
            else:
                try:
                    await interaction.user.send("測試訊息！\n"
                                                "如果你看到這則訊息，表示你的「允許陌生人傳送陌生訊息」已開啟，無須額外設定。恭喜！", delete_after=5)
                    embed.description += "、".join(selects.values)
                    json_assistant.edit_announcement_receiver(interaction.user.id, selects.values)
                    self.real_logger.info(f"{interaction.user} 訂閱了以下內容：{selects.values}")
                except discord.errors.Forbidden:
                    embed = Embed(title="錯誤", description="你似乎沒有開啟「允許陌生人傳送陌生訊息」功能。", color=error_color)
                    embed.add_field(name="疑難排解", value="請參考[這則文章]"
                                                       "(https://support.discord.com/hc/zh-tw/articles/7924992471191-"
                                                       "%E8%A8%8A%E6%81%AF%E8%AB%8B%E6%B1%82)來解決此問題後重試。")
                    embed.set_footer(text="為避免發生錯誤，機器人已自動為你取消所有訂閱。請在解決問題後重新訂閱。")
                    json_assistant.edit_announcement_receiver(interaction.user.id, [])
                    self.real_logger.info(f"{interaction.user} 取消訂閱了所有內容。")
            await interaction.followup.send(embed=embed, ephemeral=True)

    announcement = discord.SlashCommandGroup(name="announcement", description="訂閱通知相關指令。")

    @announcement.command(name="subscribe", description="訂閱/取消訂閱通知類別。")
    async def subscribe(self, ctx):
        embed = Embed(title="訂閱通知", description="請在下方選單選擇想要收到的通知。", color=default_color)
        embed.add_field(name="為什麼要訂閱通知？", value="訂閱通知可以獲得：\n"
                                                "* 📢一般公告：不定期提供使用提示、功能介紹！\n"
                                                "* 🔄️更新通知：在新指令、功能發布時，可以獲得及時通知和簡介！\n"
                                                "* 🚨緊急公告：機器人發生重大故障時，立即獲得警示！\n"
                                                "* 💬雜七雜八：聽一下Allen Why的幹話和||無病呻吟||")
        await ctx.respond(embed=embed, ephemeral=True, view=self.AnnouncementSelection(self))

    @announcement.command(name="publish", description="(開發者限定)發布公告。")
    @commands.is_owner()
    async def publish(self, ctx,
                      公告類型: Option(str, choices=["一般公告", "緊急公告", "更新通知", "雜七雜八"], description="選擇公告發布時的類型")):  # noqa
        await ctx.send_modal(self.CreateAnnouncement(self, announcement_type=公告類型))


def setup(bot):
    bot.add_cog(Announcement(bot, bot.logger))
    bot.logger.info("\"Announcement\"已被載入。")
