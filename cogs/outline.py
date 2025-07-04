# coding=utf-8
import discord
from discord.ext import commands
from discord import Embed, Option
import os
import zoneinfo
from pathlib import Path
from dotenv import load_dotenv

from outline_api import OutlineAPI


error_color = 0xF1411C
default_color = 0x5FE1EA
now_tz = zoneinfo.ZoneInfo("Asia/Taipei")
base_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = str(Path(__file__).parent.parent.absolute())


class Outline(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.outline: OutlineAPI
        self.outline = None
        self.bot = bot

        load_dotenv(os.path.join(base_dir, "TOKEN.env"))

    @commands.Cog.listener()
    async def on_ready(self):
        self.outline = OutlineAPI(os.getenv("OUTLINE_API_URL"))

    @staticmethod
    def bytes_to_human_readable_size(size_in_bytes: int) -> str:
        """
        (Generated by Google Gemini)
        將位元組大小轉換為可閱讀的格式 (KB, MB, GB, TB, PB)。

        Args:
            size_in_bytes: 以位元組為單位的整數大小。

        Returns:
            可閱讀的字串，例如 "10.5 MB"。
        """
        if size_in_bytes < 0:
            return "無效大小 (不能為負數)"

        # 定義單位和對應的進位值 (使用 1024 進位)
        units = ["B", "KB", "MB", "GB", "TB", "PB"]

        # 如果大小為 0，直接回傳 "0 B"
        if size_in_bytes == 0:
            return "0 B"

        # 計算對數以確定應該使用哪個單位
        # log(size_in_bytes, 1024) 會告訴我們 size_in_bytes 是 1024 的幾次方
        # 例如：
        # log(1023, 1024) 約為 0 (所以是 B)
        # log(1024, 1024) 為 1 (所以是 KB)
        # log(1024*1024, 1024) 為 2 (所以是 MB)
        import math
        i = int(math.floor(math.log(size_in_bytes, 1024)))

        # 確保索引不超過單位列表的範圍
        if i >= len(units):
            i = len(units) - 1  # 使用最大的單位

        # 計算轉換後的值
        human_readable_size = size_in_bytes / (1024 ** i)

        # 格式化輸出，保留兩位小數 (如果不是 B 的話)
        return f"`{human_readable_size:.2f}` {units[i]}" if i > 0 else f"`{human_readable_size}` {units[i]}"

    OUTLINE_CMDS = discord.SlashCommandGroup(
        name="outline", description="Outline VPN 相關指令"
    )

    @OUTLINE_CMDS.command(name="server_info", description="取得 Outline 伺服器的資訊。")
    @commands.is_owner()
    async def server_info(self, ctx: discord.ApplicationContext):
        response = await self.outline.get_server_info()
        embed = Embed(title="Outline 伺服器資訊", color=default_color)
        embed.add_field(name="名稱", value=response.get("name"), inline=False)
        embed.add_field(
            name="位址",
            value=f"```{response.get('hostnameForAccessKeys')}:{response.get('portForNewAccessKeys')}```",
            inline=False,
        )
        embed.add_field(name="版本", value=response.get("version"), inline=False)
        embed.add_field(name="UUID", value=response.get("serverId"), inline=False)
        await ctx.respond(embed=embed, ephemeral=True)

    @OUTLINE_CMDS.command(name="list_keys", description="取得可用的金鑰。")
    @commands.is_owner()
    async def list_keys(self, ctx: discord.ApplicationContext):
        response = await self.outline.get_access_keys()
        embed = Embed(
            title="Outline 金鑰",
            description=f"伺服器中共有 `{len(response)}` 個金鑰可用。",
            color=default_color,
        )
        for k in response:
            embed.add_field(
                name=f"金鑰 #{k.get('id')}",
                value=f"- 名稱：{k.get('name')}\n"
                f"- 密碼：||`{k.get('password')}`||\n"
                f"- 連線金鑰：||```{k.get('accessUrl')}```||",
                inline=False,
            )
        await ctx.respond(embed=embed, ephemeral=True)

    @OUTLINE_CMDS.command(name="create_new_key", description="新增金鑰。")
    @commands.is_owner()
    async def create_new_key(
        self,
        ctx: discord.ApplicationContext,
        name: Option(
            str, name="名稱", description="用於辨識金鑰", required=False
        ) = None,
        password: Option(
            str,
            name="密碼",
            description="可自訂密碼 (預設為伺服器隨機產生)",
            required=False,
        ) = None,
    ):
        try:
            response = await self.outline.create_access_key(name, password)
            embed = Embed(
                title="已產生新的金鑰",
                description="詳細資料如下：",
                color=default_color,
            )
            embed.add_field(
                name=f"金鑰 #{response.get('id')}",
                value=f"- 名稱：{response.get('name')}\n"
                f"- 密碼：||`{response.get('password')}`||\n"
                f"- 連線金鑰：||```{response.get('accessUrl')}```||",
                inline=False,
            )
        except Exception as e:
            embed = Embed(
                title="錯誤",
                description="由於未知錯誤，無法產生新的金鑰。",
                color=error_color,
            )
            embed.add_field(
                name="錯誤訊息", value=f"```{type(e).__name__}: {e}```", inline=False
            )
        await ctx.respond(embed=embed, ephemeral=True)

    @OUTLINE_CMDS.command(name="delete_key", description="移除金鑰。")
    @commands.is_owner()
    async def delete_key(
        self,
        ctx: discord.ApplicationContext,
        key_id: Option(int, name="金鑰id", description="欲移除金鑰的 ID"),
    ):
        try:
            await self.outline.delete_access_key(key_id)
            embed = Embed(
                title="已移除金鑰",
                description=f"已移除金鑰 #{key_id}。",
                color=default_color,
            )
        except Exception as e:
            embed = Embed(
                title="錯誤",
                description=f"無法移除金鑰。請確定 ID `{key_id}` 是否存在。",
                color=error_color,
            )
            embed.add_field(
                name="錯誤訊息", value=f"```{type(e).__name__}: {e}```", inline=False
            )
        await ctx.respond(embed=embed, ephemeral=True)

    @OUTLINE_CMDS.command(name="show_usage", description="顯示各金鑰所使用的流量及總流量。")
    @commands.is_owner()
    async def show_usage(self, ctx: discord.ApplicationContext):
        response = await self.outline.get_bandwidth_usage()
        embed = Embed(title="流量統計", color=default_color)
        total_usage: int = 0
        for k, v in response.items():
            embed.add_field(name=f"金鑰 #{k}", value=self.bytes_to_human_readable_size(v), inline=False)
            total_usage += v
        embed.description = f"總流量：{self.bytes_to_human_readable_size(total_usage)}"
        await ctx.respond(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(Outline(bot))
    bot.logger.info(f'"{Outline.__name__}"已被載入。')
