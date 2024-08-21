# coding=utf-8
import time
import datetime
import discord
from discord.ext import commands
from discord import (
    Embed,
    Option,
    ui,
    SelectOption,
    ButtonStyle,
    FFmpegPCMAudio,
    PCMVolumeTransformer,
)
import os
from shutil import copyfile
import zoneinfo
from pathlib import Path
import aiohttp
import aiofiles
import audioread
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

HISTORY: list[dict] = []


class Soundboard(commands.Cog):
    def __init__(self, bot: commands.Bot, real_logger: logger.CreateLogger):
        self.bot = bot
        self.real_logger = real_logger

    @commands.Cog.listener()
    async def on_guild_available(self, guild: discord.Guild):
        path = os.path.join(sound_dir, str(guild.id))
        try:
            os.mkdir(path)
            self.real_logger.info("新增資料夾：" + path)
        except OSError:
            self.real_logger.debug(path + " 已存在，不須新增")

    def soundboard_selection(
        self,
        ctx,
        is_general: bool,
        mode: str = "play",
        copy_server: discord.Guild = None,
    ) -> ui.View:
        view = ui.View(timeout=600, disable_on_timeout=True)
        replay_btn = ui.Button(
            emoji="🔄", label="重播", style=ButtonStyle.green, disabled=True
        )
        if mode == "play":
            soundboard = SoundboardIndex(None if is_general else ctx.guild.id)
        elif mode == "remove":
            soundboard = SoundboardIndex(ctx.guild.id)
        elif mode == "copy":
            soundboard = SoundboardIndex(copy_server.id)
        else:
            soundboard = SoundboardIndex()
        sounds = soundboard.get_sounds()
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

        async def menu_callback(interaction: discord.Interaction):
            await interaction.response.defer()
            if len(menu.values) == 0:
                return
            selected_sound = sounds[int(menu.values[0])]
            if mode == "play":
                check_vc_result = await Events.check_voice_channel(
                    self, ctx.guild, [ctx.author.id], connect_when_found=False
                )
                if isinstance(check_vc_result, str):
                    embed = Embed(
                        title="錯誤", description="機器人自動加入語音頻道時失敗。", color=error_color
                    )
                    embed.add_field(name="錯誤訊息", value=check_vc_result)
                    await interaction.followup.send(embed=embed, ephemeral=True)
                elif isinstance(check_vc_result, discord.VoiceChannel):
                    try:
                        vc_client = None
                        for vc in self.bot.voice_clients:
                            if vc.channel.id == check_vc_result.id:  # noqa
                                vc_client = vc
                            elif (
                                vc.channel.guild.id == check_vc_result.guild.id  # noqa
                            ):
                                await vc.disconnect(force=False)
                                break
                        if vc_client is None:
                            vc_client = await check_vc_result.connect()
                            await check_vc_result.guild.change_voice_state(
                                channel=check_vc_result, self_mute=False, self_deaf=True
                            )
                        vc_client.play(
                            PCMVolumeTransformer(
                                original=FFmpegPCMAudio(
                                    source=selected_sound["file_path"]
                                ),
                                volume=0.3,
                            )
                        )
                        HISTORY.append(
                            {
                                "timestamp": time.time(),
                                "user_id": interaction.user.id,
                                "vc_id": check_vc_result.id,
                                "sound_display_name": selected_sound["display_name"],
                            }
                        )
                        replay_btn.disabled = False
                        embed = Embed(
                            title="播放完成！", description="已播放所選取的音效。", color=default_color
                        )
                        embed.add_field(name="名稱", value=selected_sound["display_name"])
                        await interaction.edit_original_response(view=view)
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
                        embed.add_field(
                            name="錯誤訊息", value=f"```{str(e)}```", inline=False
                        )
                    await interaction.followup.send(embed=embed, ephemeral=True)
            elif mode == "remove":
                soundboard.remove_sound(sounds.index(selected_sound))
                embed = Embed(
                    title="已移除音效",
                    description=f"已從「{interaction.guild.name}」移除了音效「{selected_sound['display_name']}」。",
                    color=default_color,
                )
                await interaction.edit_original_response(embed=embed, view=None)
            elif mode == "copy":
                destination_server_soundboard = SoundboardIndex(ctx.guild.id)
                copied_sound_path = os.path.join(
                    sound_dir, str(ctx.guild.id), selected_sound["file_path"][-9:]
                )
                copyfile(selected_sound["file_path"], copied_sound_path)
                destination_server_soundboard.add_sound(
                    display_name=selected_sound["display_name"],
                    description=selected_sound["description"],
                    file_path=copied_sound_path,
                )
                embed = Embed(
                    title="複製完成！",
                    description=f"已複製「{copy_server.name}」的音效「{selected_sound['display_name']}」。",
                    color=default_color,
                )
                await interaction.edit_original_response(embed=embed, view=None)

        async def btn_callback(interaction: discord.Interaction):
            if len(menu.values) == 0:
                embed = Embed(
                    title="錯誤：未選取音效",
                    description="你尚未在選單中選取音效，因此無法重播。",
                    color=error_color,
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await menu_callback(interaction)

        menu.callback = menu_callback
        replay_btn.callback = btn_callback

        view.add_item(menu)
        view.add_item(replay_btn)
        return view

    def add_sound_window(self, is_general: bool) -> ui.View:
        view = ui.View(disable_on_timeout=True)
        btn = ui.Button(label="已取得URL，新增音效", style=ButtonStyle.green, emoji="🔗")
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
            if is_general:
                soundboard_index = SoundboardIndex()
            else:
                soundboard_index = SoundboardIndex(interaction.guild.id)
            if window.children[0].value in soundboard_index.get_sound_display_name():
                embed = Embed(
                    title="錯誤：名稱重複",
                    description=f"你所提供的音效名稱(`{window.children[0].value}`)已經存在。",
                    color=error_color,
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            file_url = window.children[2].value
            if file_url.startswith("https://cdn.discordapp.com/attachments/"):
                async with aiohttp.ClientSession() as session:
                    async with session.get(file_url) as response:
                        if response.status == 200:
                            random_char_list = [choice(hexdigits) for _ in range(5)]
                            file_name = "".join(random_char_list) + ".snd"
                            file_path = os.path.join(
                                sound_dir,
                                "general" if is_general else str(interaction.guild.id),
                                file_name,
                            )
                            file = await aiofiles.open(file_path, mode="wb")
                            await file.write(await response.read())
                            await file.close()
                            try:
                                audio_file = audioread.audio_open(file_path)
                                length = audio_file.duration
                                if length <= 15:
                                    self.real_logger.info(
                                        f"{interaction.user.name} 新增了音效"
                                    )
                                    self.real_logger.info(
                                        "   ⌊伺服器：" + interaction.guild.name
                                    )
                                    self.real_logger.info(
                                        "   ⌊音效名稱：" + window.children[0].value
                                    )
                                    self.real_logger.info("   ⌊音效檔案路徑：" + file_path)
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
                                        title="錯誤：音檔長度超過限制",
                                        description=f"你所上傳的音檔長度(`{length}` 秒)超過15秒限制。",
                                        color=error_color,
                                    )
                                    os.remove(file_path)
                            except audioread.exceptions.NoBackendError:
                                embed = Embed(
                                    title="錯誤：非音檔",
                                    description="機器人解碼檔案時失敗，可能是檔案類型錯誤造成。",
                                    color=error_color,
                                )
                                os.remove(file_path)
                            except Exception as e:
                                embed = Embed(
                                    title="錯誤",
                                    description="發生未知錯誤。",
                                    color=error_color,
                                )
                                embed.add_field(
                                    name="錯誤訊息", value=f"```{str(e)}```", inline=False
                                )
                                os.remove(file_path)
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
        is_general: Option(
            bool, name="使用通用音效", description="是否要使用通用音效，而非伺服器音效", required=False
        ) = False,
    ):
        await ctx.defer()
        description = "從下方的選單選取要播放的音效。\n播放結束後，如果還要播放其他音效，請取消選取原本的選擇再重新選取即可。"
        if is_general:
            description += "\n⚠️**注意：目前為通用音效！**"
        embed = Embed(
            title="播放音效",
            description=description,
            color=default_color,
        )
        embed.set_footer(text="本功能目前測試中，可能不會正常運作。")
        await ctx.respond(embed=embed, view=self.soundboard_selection(ctx, is_general))

    @SOUNDBOARD_CMDS.command(name="add", description="新增音效。")
    @commands.has_permissions(manage_guild=True)
    async def soundboard_add(
        self,
        ctx: discord.ApplicationContext,
        is_general: Option(
            bool, name="上傳通用音效", description="是否要上傳為通用音效，而非伺服器音效", required=False
        ) = False,
    ):
        await ctx.defer(ephemeral=True)
        soundboard = SoundboardIndex(None if is_general else ctx.guild.id)
        if is_general and ctx.author.id != 657519721138094080:
            embed = Embed(
                title="錯誤：非機器人擁有者",
                description="僅有 <@657519721138094080> 可上傳通用音效。",
                color=error_color,
            )
            await ctx.respond(embed=embed, ephemeral=True)
        elif len(soundboard.get_sounds()) >= 25:
            embed = Embed(
                title="錯誤：已達音效數量限制", description="已經達到25個音效的限制。", color=error_color
            )
            await ctx.respond(embed=embed, ephemeral=True)
        else:
            description = "取得音檔URL後，點擊下方按鈕以新增音效。"
            if is_general:
                description += "\n⚠️**注意：你即將上傳為通用音效！**"
            embed = Embed(
                title="新增音效",
                description=description,
                color=default_color,
            )
            embed.add_field(
                name="音效額度",
                value=f"已使用 {len(soundboard.get_sounds())} / 25 個",
                inline=False,
            )
            embed.add_field(
                name="1. 在Discord上傳音效",
                value="在Discord的任一頻道上傳音檔。\n__**(注意：務必在Discord上傳音檔！)**__",
                inline=False,
            )
            embed.add_field(name="2. 複製連結", value="對音檔點擊右鍵，並點擊「複製連結」。", inline=False)
            embed.add_field(name="3. 開啟上傳視窗", value="點擊下方按鈕，繼續新增音效流程。", inline=False)
            await ctx.respond(
                embed=embed, view=self.add_sound_window(is_general), ephemeral=True
            )

    @SOUNDBOARD_CMDS.command(name="remove", description="移除音效。")
    @commands.has_permissions(manage_guild=True)
    async def soundboard_remove(
        self,
        ctx: discord.ApplicationContext,
    ):
        await ctx.defer(ephemeral=True)
        embed = Embed(
            title="移除音效",
            description="從下方的選單選取要移除的音效。\n**注意：音效移除後即無法復原！**",
            color=default_color,
        )
        await ctx.respond(
            embed=embed,
            view=self.soundboard_selection(ctx, False, "remove"),
            ephemeral=True,
        )

    @SOUNDBOARD_CMDS.command(name="copy", description="(開發者限定)複製其他伺服器的音效至此伺服器。")
    @commands.is_owner()
    async def soundboard_copy(
        self,
        ctx: discord.ApplicationContext,
        target_guild_id: Option(
            str, name="伺服器id", description="欲複製音效的伺服器ID", required=True
        ),
    ):
        await ctx.defer(ephemeral=True)
        if not target_guild_id.isdigit():
            embed = Embed(
                title="錯誤：ID無效",
                description=f"你所輸入的ID`{target_guild_id}`無效。",
                color=error_color,
            )
            await ctx.respond(embed=embed)
        else:
            target_guild_id = int(target_guild_id)
            if target_guild_id == ctx.guild.id:
                embed = Embed(
                    title="錯誤：同伺服器",
                    description=f"ID`{target_guild_id}`是目前伺服器的ID。你不能在同一伺服器中複製音效。",
                    color=error_color,
                )
                await ctx.respond(embed=embed)
            else:
                copy_server = self.bot.get_guild(target_guild_id)
                if copy_server is None:
                    embed = Embed(
                        title="錯誤：無法取得伺服器",
                        description=f"無法透過ID`{target_guild_id}`取得伺服器。",
                        color=error_color,
                    )
                    await ctx.respond(embed=embed)
                elif len(SoundboardIndex(target_guild_id).get_sounds()) >= 25:
                    embed = Embed(
                        title="錯誤：已達音效數量限制",
                        description="已經達到25個音效的限制。",
                        color=error_color,
                    )
                    await ctx.respond(embed=embed, ephemeral=True)
                else:
                    embed = Embed(
                        title="複製音效",
                        description=f"從下方的選單選取要從「{copy_server.name}」複製的音效。",
                        color=default_color,
                    )
                    await ctx.respond(
                        embed=embed,
                        view=self.soundboard_selection(ctx, False, "copy", copy_server),
                    )

    @SOUNDBOARD_CMDS.command(name="history", description="顯示最近25次的音效播放紀錄。")
    async def soundboard_history(self, ctx):
        latest_25_history = HISTORY
        if len(HISTORY) > 25:
            latest_25_history = HISTORY[-25:]
        embed = Embed(
            title="音效播放紀錄", description="下方列出了最近25次的音效播放紀錄。", color=default_color
        )
        if len(latest_25_history) != 0:
            for record in latest_25_history:
                embed.add_field(
                    name=datetime.datetime.fromtimestamp(record["timestamp"]).strftime("%Y/%m/%d %H:%M:%S"),
                    value=f"使用者：<@{record['user_id']}>\n"
                          f"語音頻道：<#{record['vc_id']}>\n"
                          f"播放音效：{record['sound_display_name']}",
                    inline=False
                )
        else:
            embed.add_field(name=" ", value="(無紀錄)", inline=False)
        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(Soundboard(bot, bot.logger))
    bot.logger.info(f'"{Soundboard.__name__}"已被載入。')
