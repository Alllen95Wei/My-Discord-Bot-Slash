# coding=utf-8
import discord
from discord.ext import commands
from discord import Embed, Option, ui, SelectOption, ButtonStyle, FFmpegPCMAudio
import os
import zoneinfo
from pathlib import Path
import aiohttp
import aiofiles
from random import choice
from string import hexdigits

import logger
from cogs.general import Events
from json_assistant import SoundboardIndex


error_color = 0xF1411C
default_color = 0x5FE1EA
now_tz = zoneinfo.ZoneInfo("Asia/Taipei")
base_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = str(Path(__file__).parent.parent.absolute())
sound_dir = os.path.join(parent_dir, "soundboard_data")


class Soundboard(commands.Cog):
    def __init__(self, bot: commands.Bot, real_logger: logger.CreateLogger):
        self.bot = bot
        self.real_logger = real_logger

        for guild in bot.guilds:
            os.mkdir(os.path.join(sound_dir, str(guild.id)))

    def soundboard_selection(self, ctx) -> ui.View:
        view = ui.View(timeout=300, disable_on_timeout=True)
        sounds = SoundboardIndex(ctx.guild.id).get_sounds()
        selections = []
        menu = ui.Select(
            placeholder="選取音效",
            min_values=0,
            max_values=1,
        )
        if len(sounds) > 0:
            for sound in sounds:
                selections.append(
                    SelectOption(
                        label=sound["display_name"],
                        value=str(sounds.index(sound)),
                        description=sound["description"]
                        if sound["description"]
                        else "(無說明)",
                    )
                )
        else:
            menu.placeholder = "(無可用的音效)"
            selections.append(SelectOption(label="(無可用的音效)"))
            menu.disabled = True
        menu.options = selections

        async def callback(interaction: discord.Interaction):
            await interaction.response.defer()
            if len(menu.values) == 0:
                return
            selected_sound = sounds[int(menu.values[0])]
            check_vc_result = await Events.check_voice_channel(
                self, ctx.guild, [ctx.author.id], connect_when_found=False
            )
            embed = Embed(
                title="This is a dummy",
                description="This is a dummy embed. You shouldn't see this.",
            )
            if isinstance(check_vc_result, str):
                embed = Embed(
                    title="錯誤", description="機器人自動加入語音頻道時失敗。", color=error_color
                )
                embed.add_field(name="錯誤訊息", value=check_vc_result)
            elif isinstance(check_vc_result, discord.VoiceChannel):
                try:
                    vc_client = None
                    for vc in self.bot.voice_clients:
                        if vc.channel.id == check_vc_result.id:  # noqa
                            vc_client = vc
                    if vc_client is None:
                        vc_client = await check_vc_result.connect()
                    vc_client.play(FFmpegPCMAudio(source=selected_sound["file_path"]))
                    embed = Embed(
                        title="播放完成！", description="已播放所選取的音效。", color=default_color
                    )
                    embed.add_field(name="名稱", value=selected_sound["display_name"])
                except discord.errors.ClientException as e:
                    if str(e) == "Already playing audio.":
                        embed = Embed(
                            title="錯誤：目前播放中",
                            description="目前已在播放其他音效。",
                            color=error_color,
                        )
                    else:
                        embed = Embed(
                            title="錯誤：未連接至語音頻道",
                            description="機器人自動加入語音頻道時失敗。",
                            color=error_color,
                        )
                        embed.add_field(
                            name="錯誤訊息", value=f"```{str(e)}```", inline=False
                        )
                except Exception as e:
                    embed = Embed(
                        title="錯誤",
                        description="發生未知錯誤。",
                        color=error_color,
                    )
                    embed.add_field(name="錯誤訊息", value=f"```{str(e)}```", inline=False)
            await interaction.followup.send(embed=embed, ephemeral=True)

        menu.callback = callback

        view.add_item(menu)
        return view

    @staticmethod
    def add_sound_window() -> ui.View:
        view = ui.View()
        btn = ui.Button(label="已取得URL，新增音效", style=ButtonStyle.green)
        window = ui.Modal(
            ui.InputText(label="音效名稱", max_length=20),
            ui.InputText(label="說明", max_length=100, required=False),
            ui.InputText(
                label="貼上檔案URL",
                placeholder="https://cdn.discordapp.com/attachments/...",
            ),
            title="新增音效",
        )

        async def window_callback(interaction: discord.Interaction):
            await interaction.response.defer()
            file_url = window.children[2].value
            if file_url.startswith("https://cdn.discordapp.com/attachments/"):
                async with aiohttp.ClientSession() as session:
                    async with session.get(file_url) as response:
                        if response.status == 200:
                            random_char_list = [choice(hexdigits) for _ in range(5)]
                            file_name = "".join(random_char_list) + ".snd"
                            file_path = os.path.join(
                                sound_dir,
                                str(interaction.guild.id),
                                file_name,
                            )
                            file = await aiofiles.open(file_path, mode="wb")
                            await file.write(await response.read())
                            await file.close()
                            soundboard_index = SoundboardIndex(interaction.guild.id)
                            soundboard_index.add_sound(
                                display_name=window.children[0].value,
                                description=window.children[1].value,
                                file_path=file_path,
                            )
                            embed = Embed(
                                title="新增成功！",
                                description="你的音效已上傳完成，現已能透過機器人使用。",
                                color=default_color,
                            )
                            embed.add_field(
                                name="音效名稱",
                                value=window.children[0].value,
                                inline=False,
                            )
                            embed.add_field(
                                name="說明",
                                value=window.children[1].value
                                if window.children[1].value
                                else "(無說明)",
                                inline=False,
                            )
                        else:
                            embed = Embed(
                                title=f"錯誤：HTTP {response.status}",
                                description="下載時的回應碼不正常。",
                                color=error_color,
                            )
                            embed.add_field(
                                name="錯誤訊息", value="```" + await response.text() + "```"
                            )
                        await interaction.edit_original_response(embed=embed, view=None)
            else:
                embed = Embed(
                    title="錯誤：URL不來自Discord",
                    description="你所提供的連結不是來自Discord。請透過Discord上傳檔案、取得URL後再試一次。",
                    color=error_color,
                )
                await interaction.followup.send(embed=embed, ephemeral=True)

        async def btn_callback(interaction: discord.Interaction):
            await interaction.response.send_modal(window)

        window.callback = window_callback

        btn.callback = btn_callback

        view.add_item(btn)

        return view

    SOUNDBOARD_CMDS = discord.SlashCommandGroup(name="soundboard")

    @SOUNDBOARD_CMDS.command(name="play", description="播放指定的音效。")
    async def soundboard_play(
        self,
        ctx: discord.ApplicationContext,
    ):
        await ctx.defer()
        embed = Embed(
            title="選取音效",
            description="從下方的選單選取要播放的音效。\n播放結束後，如果還要播放其他音效，請取消選取原本的選擇再重新選取即可。",
            color=default_color,
        )
        embed.set_footer(text="本功能目前測試中。")
        await ctx.respond(embed=embed, view=self.soundboard_selection(ctx))

    @SOUNDBOARD_CMDS.command(name="add", description="新增音效。")
    @commands.has_permissions(manage_guild=True)
    async def soundboard_add(
        self,
        ctx: discord.ApplicationContext,
    ):
        await ctx.defer(ephemeral=True)
        embed = Embed(
            title="新增音效", description="取得音檔URL後，點擊下方按鈕以在這個伺服器新增音效。", color=default_color
        )
        embed.add_field(
            name="1. 在Discord上傳音效",
            value="在Discord的任一頻道上傳音檔。\n__**(注意：務必在Discord上傳音檔！)**__",
            inline=False,
        )
        embed.add_field(name="2. 複製連結", value="對音檔點擊右鍵，並點擊「複製連結」。", inline=False)
        embed.add_field(name="3. 開啟上傳視窗", value="點擊下方按鈕，繼續新增音效流程。", inline=False)
        await ctx.respond(embed=embed, view=self.add_sound_window(), ephemeral=True)


def setup(bot):
    bot.add_cog(Soundboard(bot, bot.logger))
    bot.logger.info(f'"{Soundboard.__name__}"已被載入。')
