# coding=utf-8
import discord
from discord.ext import commands
from discord import Embed, Option
import os
import zoneinfo
from pathlib import Path
import aiofiles
from aiohttp import ClientSession
from magika import Magika
from http.cookiejar import MozillaCookieJar, LoadError

import logger
import json_assistant


error_color = 0xF1411C
default_color = 0x5FE1EA
now_tz = zoneinfo.ZoneInfo("Asia/Taipei")
base_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = str(Path(__file__).parent.parent.absolute())


class Config(commands.Cog):
    def __init__(self, bot: commands.Bot, real_logger: logger.CreateLogger):
        self.bot = bot
        self.real_logger = real_logger

    # main command group
    CONFIG_CMD = discord.SlashCommandGroup(name="config", description="設定機器人的相關功能。")

    # sub command groups
    EXP_CONFIG = CONFIG_CMD.create_subgroup(name="exp_sys", description="經驗值系統相關設定")
    MUSICDL_CONFIG = CONFIG_CMD.create_subgroup(
        name="musicdl", description="YouTube下載相關設定"
    )

    @EXP_CONFIG.command(name="set_upgrade_notify", description="經驗值系統：設定傳送升等通知的時機")
    async def set_upgrade_notify(
        self,
        ctx,
        text_lvl: Option(
            int,
            name="文字等級",
            description="每升級幾次文字等級，才傳送升等通知？(輸入0以保留原先設定)",
            min_value=0,
            max_value=50,
            required=True,
        ),
        voice_lvl: Option(
            int,
            name="語音等級",
            description="每升級幾次語音等級，才傳送升等通知？(輸入0以保留原先設定)",
            min_value=0,
            max_value=50,
            required=True,
        ),
    ):
        user_obj = json_assistant.User(ctx.author.id)
        original_threshold = user_obj.get_notify_threshold()
        if text_lvl == 0:
            text_lvl = original_threshold["text"]
        if voice_lvl == 0:
            voice_lvl = original_threshold["voice"]
        user_obj.set_notify_threshold(text_lvl, voice_lvl)
        self.real_logger.info(f"設定：{ctx.author.name} 設定了傳送升等通知的時機")
        self.real_logger.info(f"   ⌊文字等級：`{original_threshold['text']}`等 → `{text_lvl}`等")
        self.real_logger.info(f"   ⌊語音等級：`{original_threshold['voice']}`等 → `{voice_lvl}`等")
        embed = Embed(title="設定完成", description="已重新設定升等通知。", color=default_color)
        embed.add_field(
            name="文字",
            value=f"`{original_threshold['text']}`等 ➡️ `{text_lvl}`等\n"
            f"現在起，文字等級每升`{text_lvl}`等才會傳送通知。",
            inline=False,
        )
        embed.add_field(
            name="語音",
            value=f"`{original_threshold['voice']}`等 ➡️ `{voice_lvl}`等\n"
            f"現在起，語音等級每升`{voice_lvl}`等才會傳送通知。",
            inline=False,
        )
        await ctx.respond(embed=embed)

    @EXP_CONFIG.command(
        name="set_voice_exp_report", description="經驗值系統：設定結束語音階段時，是否要傳送經驗值報告"
    )
    async def set_voice_exp_report(
        self,
        ctx,
        enabled: Option(bool, name="啟用", description="是否啟用經驗值報告", required=True),
    ):
        user_obj = json_assistant.User(ctx.author.id)
        user_obj.set_exp_report_enabled(enabled)
        self.real_logger.info(f"設定：{ctx.author.name} 設定了語音經驗值報告")
        self.real_logger.info(f"   ⌊傳送語音經驗值報告：{'啟用' if enabled else '停用'}")
        embed = Embed(
            title="設定完成",
            description=f"已 **{'啟用' if enabled else '停用'}** 語音經驗值報告。",
            color=default_color,
        )
        await ctx.respond(embed=embed)

    @MUSICDL_CONFIG.command(name="upload_cookie", description="YouTube下載：上傳自己的cookie檔案")
    async def upload_cookie(
        self,
        ctx,
        cookie: Option(
            discord.Attachment,
            name="cookie檔案",
            description="上傳匯出的cookies.txt",
            required=True,
        ),
    ):
        await ctx.defer(ephemeral=True)
        self.real_logger.info(f"設定：{ctx.author.name} 上傳了cookie檔案")
        cookie: discord.Attachment
        file_url = cookie.url
        self.real_logger.debug("URL: " + file_url)
        async with ClientSession() as session:
            async with session.get(file_url) as response:
                self.real_logger.debug(f"Result: HTTP {response.status}")
                if response.status == 200:
                    file_path = os.path.join(
                        parent_dir, "cookies", str(ctx.author.id) + ".txt"
                    )
                    async with aiofiles.open(file_path, "wb+") as f:
                        await f.write(await response.read())
                    detect_result = Magika().identify_path(Path(file_path)).output
                    file_type = detect_result.mime_type
                    score = detect_result.score
                    delete_file = False
                    if file_type == "text/plain":
                        try:
                            cookie_jar = MozillaCookieJar(file_path)
                            cookie_jar.load()
                            embed = Embed(
                                title="成功：cookie格式正確",
                                description="你上傳的cookie檔案已通過格式驗證！下次使用`/musicdl`指令時，機器人即會使用此cookie檔案。\n"
                                "⚠️**請注意：即使通過格式驗證，你的cookie仍有可能因為過期等因素而無法使用。**",
                                color=default_color,
                            )
                            self.real_logger.info("   ⌊結果：成功 (檔案類型正確、格式正確)")
                        except LoadError:
                            embed = Embed(
                                title="錯誤：cookie格式錯誤",
                                description="你所上傳的cookie檔案似乎不符合格式。",
                                color=error_color,
                            )
                            delete_file = True
                            self.real_logger.info("   ⌊結果：失敗 (檔案類型正確、格式錯誤)")
                        except Exception as e:
                            embed = Embed(
                                title="錯誤", description="發生未知錯誤。", color=error_color
                            )
                            embed.add_field(
                                name="錯誤訊息", value=f"```{e}```", inline=False
                            )
                            delete_file = True
                            self.real_logger.info("   ⌊結果：失敗 (檔案類型正確、格式未知)")
                            self.real_logger.warning(f"   ⌊錯誤訊息：{type(e).__name__}: {str(e)}")
                    else:
                        embed = Embed(
                            title="錯誤：檔案類型錯誤",
                            description="你所上傳的cookie檔案似乎不是文字檔(`text/plain`)。",
                            color=error_color,
                        )
                        embed.add_field(
                            name="Debug: File type",
                            value="`" + file_type + "`",
                            inline=False,
                        )
                        embed.add_field(
                            name="Debug: Score",
                            value="`%.2f %%`" % (score * 100),
                            inline=False,
                        )
                        delete_file = True
                        self.real_logger.info("   ⌊結果：失敗 (檔案類型錯誤)")
                    if delete_file:
                        os.remove(file_path)
                        self.real_logger.debug("刪除有誤的檔案：" + file_path)
                else:
                    self.real_logger.info(f"   ⌊結果：失敗 (HTTP {response.status})")
                    embed = Embed(title=f"錯誤：HTTP {response.status}", description="下載檔案時發生錯誤。", color=error_color)
                    embed.add_field(
                        name="Debug: Response",
                        value=f"```{response.text()}```",
                        inline=False,
                    )
        await ctx.respond(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(Config(bot, bot.logger))
    bot.logger.info(f'"{Config.__name__}"已被載入。')
