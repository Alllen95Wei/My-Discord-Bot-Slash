import discord
from discord.ext import commands
from discord import Option
import os
from dotenv import load_dotenv
from random import choice
from random import randint
from shlex import split
from subprocess import run
from platform import system

import check_folder_size
from youtube_to_mp3 import main_dl
import detect_pc_status
import update

intents = discord.Intents.all()
bot = commands.Bot(intents=intents)
base_dir = os.path.abspath(os.path.dirname(__file__))
default_color = 0x5FE1EA
error_color = 0xF1411C


async def check_voice_channel():
    # 列出所有語音頻道
    voice_channel_lists = []
    for server in bot.guilds:
        for channel in server.channels:
            if channel.type == discord.ChannelType.voice:
                voice_channel_lists.append(channel)
                print(server.name + "/" + channel.name)
                members = channel.members
                # msg = ""
                # 列出所有語音頻道的成員
                for member in members:
                    print("   ⌊" + member.name)
                    if member == bot.get_user(885723595626676264) or member == bot.get_user(657519721138094080):
                        # 若找到Allen Music Bot或Allen Why，則嘗試加入該語音頻道
                        try:
                            await channel.guild.change_voice_state(channel=channel, self_mute=True, self_deaf=True)
                            # msg = "加入語音頻道：" + server.name + "/" + channel.name
                            # log_writter.write_log(msg)
                            return channel.id
                        except Exception as e:
                            # msg = "加入語音頻道失敗：" + server.name + "/" + channel.name + "(" + str(e) + ")"
                            # log_writter.write_log(msg)
                            if str(e) == "Already connected to a voice channel.":
                                return "已經連線至語音頻道。"
                            else:
                                return str(e)
                    else:
                        return None


@bot.event
async def on_ready():
    await bot.sync_commands(commands=None)
    print("機器人準備完成！")
    print(f"PING值：{round(bot.latency * 1000)}ms")
    print(f"登入身分：{bot.user.name}#{bot.user.discriminator}")


@bot.slash_command(name="ama", description="就是8號球，給你這個問題的隨機回答。")
async def ama(ctx,
              問題: Option(str, "你要問的問題", required=True),
              私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):
    ans1 = ("g", "s", "b")
    ans_g = ("看起來不錯喔", "肯定的", "我覺得可行", "絕對OK", "是的", "確定", "200 OK", "100 Continue",
             "Just do it")
    ans_s = (
        "現在別問我", "404 Not Found", "你的問題超出宇宙的範圍了", "答案仍在變化", "400 Bad Request",
        "這問題實在沒人答得出來",
        "Answer=A=Ans=答案",
        "最好不要現在告訴你", "300 Multiple Choices", "去問瑪卡巴卡更快",
        "您撥的電話無人接聽，嘟聲後開始計費。", "對不起，您播的號碼是空號，請查明後再撥。")

    ans_b = (
        "不可能", "否定的", "不值得", "等等等等", "No no no", "我拒絕", "我覺得不行耶", "403 Forbidden", "這樣不好")

    ball_result1 = choice(ans1)
    if ball_result1 == "g":
        ball_result2 = choice(ans_g)
    elif ball_result1 == "s":
        ball_result2 = choice(ans_s)
    else:
        ball_result2 = choice(ans_b)
    embed = discord.Embed(title="8號球", description=f"你的問題：{問題}", color=default_color)
    embed.add_field(name="回答", value=f"\"{ball_result2}\"", inline=False)
    await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="random", description="在指定數字範圍隨機取得一數，不指定範圍則設為1~100。")
async def random(ctx,
                 range_min: Option(name="min", description="最小值", required=False, input_type=int) = 1,
                 range_max: Option(name="max", description="最大值", required=False, input_type=int) = 100,
                 私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):
    ans = randint(range_min, range_max)
    embed = discord.Embed(title="隨機", description=f"數字範圍：{range_min}~{range_max}", color=default_color)
    embed.add_field(name="結果", value=f"\"{ans}\"", inline=False)
    await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="qrcode", description="將輸入的文字轉為QR Code。")
async def qrcode(ctx,
                 內容: Option(str, "要轉換的文字", required=True),
                 私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):
    import urllib.parse
    text = urllib.parse.quote(內容)
    url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={text}"
    embed = discord.Embed(title="QR Code", description=f"內容：{內容}", color=default_color)
    embed.set_image(url=url)
    await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="sizecheck", description="檢查\"C:\\MusicBot\\audio_cache\"的大小。")
async def sizecheck(ctx,
                    私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):
    size = check_folder_size.check_size()
    embed = discord.Embed(title="資料夾大小", description=f"\"C:\\MusicBot\\audio_cache\"的大小：{size}",
                          color=default_color)
    await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="ytdl", description="將YouTube影片下載為mp3。由於Discord有"
                                            "檔案大小限制，因此有時可能會失敗。")
async def ytdl(ctx,
               url: Option(str, "欲下載的YouTube影片網址", required=True),
               私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):
    file_name = str(ctx.author) + url[-11:]
    if main_dl(url, file_name, file_name + ".mp3") == "finished":
        try:
            await ctx.respond(file=discord.File(file_name + ".mp3"), ephemeral=私人訊息)
        except Exception as e:
            if "Payload Too Large" in str(e):
                embed = discord.Embed(title="錯誤", description="檔案過大，無法上傳。", color=error_color)
                embed.add_field(name="錯誤訊息", value=f"```{e}```", inline=False)
            else:
                embed = discord.Embed(title="錯誤", description="發生未知錯誤。", color=error_color)
                embed.add_field(name="錯誤訊息", value=f"```{e}```", inline=False)
            await ctx.respond(embed=embed, ephemeral=私人訊息)
    else:
        embed = discord.Embed(title="錯誤", description="發生未知錯誤。", color=error_color)
        await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="rc",
                   description="重新連接至語音頻道。可指定頻道，否則將自動檢測音樂機器人及Allen Why在哪個頻道並加入。")
async def rc(ctx,
             頻道: Option(discord.VoiceChannel, "指定要加入的頻道", required=False),
             私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):
    if 頻道 is None:
        msg = await check_voice_channel()
        if isinstance(msg, int):
            embed = discord.Embed(title="已加入頻道", description=f"已經加入了 <#{msg}>！", color=default_color)
        elif isinstance(msg, str):
            embed = discord.Embed(title="錯誤", description="發生錯誤：`" + msg + "`", color=error_color)
        elif msg is None:
            embed = discord.Embed(title="錯誤",
                                  description="找不到<@885723595626676264>及<@657519721138094080>在哪個頻道。",
                                  color=error_color)
        else:
            embed = discord.Embed(title="錯誤", description="發生未知錯誤。", color=error_color)
    else:
        try:
            await 頻道.guild.change_voice_state(channel=頻道, self_mute=True, self_deaf=True)
            embed = discord.Embed(title="已加入頻道", description=f"已經加入了 <#{頻道.id}>！", color=default_color)
        except Exception as e:
            embed = discord.Embed(title="錯誤", description="發生錯誤：`" + str(e) + "`", color=error_color)
    await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="dc", description="從目前的語音頻道中斷連接。")
async def dc(ctx,
             私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):
    try:
        await ctx.guild.change_voice_state(channel=None)
        embed = discord.Embed(title="已斷開連接", description="已經從語音頻道中斷連接。", color=default_color)
    except Exception as e:
        if str(e) == "'NoneType' object has no attribute 'disconnect'":
            embed = discord.Embed(title="錯誤", description="目前沒有連接到任何語音頻道。", color=error_color)
        else:
            embed = discord.Embed(title="錯誤", description="發生錯誤：`" + str(e) + "`", color=error_color)
    await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="dps", description="查詢伺服器電腦的CPU及記憶體使用率。")
async def dps(ctx,
              私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):
    embed = discord.Embed(title="伺服器電腦資訊", color=default_color)
    embed.add_field(name="CPU使用率", value=f"{detect_pc_status.get_cpu_usage()}%")
    embed.add_field(name="記憶體使用率", value=f"{detect_pc_status.get_ram_usage_detail()}%")
    await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="ping", description="查詢機器人PING值(ms)。")
async def ping(ctx,
               私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):
    embed = discord.Embed(title="PONG!✨", color=default_color)
    embed.add_field(name="PING值", value=f"`{round(bot.latency * 1000)}` ms")
    await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="cmd", description="在伺服器端執行指令並傳回結果。")
async def cmd(ctx,
              指令: Option(str, "要執行的指令", required=True),
              私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):
    if ctx.author == bot.get_user(657519721138094080):
        try:
            command = split(指令)
            result = str(run(command, capture_output=True, text=True).stdout)
            if result != "":
                embed = discord.Embed(title="執行結果", description=f"```{result}```", color=default_color)
            else:
                embed = discord.Embed(title="執行結果", description="終端未傳回回應。", color=default_color)
        except WindowsError as e:
            if e.winerror == 2:
                embed = discord.Embed(title="錯誤", description="找不到指令。", color=error_color)
            else:
                embed = discord.Embed(title="錯誤", description=f"發生錯誤：`{e}`", color=error_color)
        except Exception as e:
            embed = discord.Embed(title="錯誤", description=f"發生錯誤：`{e}`", color=error_color)
    else:
        embed = discord.Embed(title="錯誤", description="你沒有權限使用此指令。", color=error_color)
        私人訊息 = True
    await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="update", description="更新機器人。")
async def update(ctx,
                 私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):
    if ctx.author == bot.get_user(657519721138094080):
        embed = discord.Embed(title="更新中", description="更新流程啟動。", color=default_color)
        await ctx.respond(embed=embed, ephemeral=私人訊息)
        event = discord.Activity(type=discord.ActivityType.playing, name="更新中...")
        await bot.change_presence(status=discord.Status.do_not_disturb, activity=event)
        update.update(os.getpid(), system())
    else:
        embed = discord.Embed(title="錯誤", description="你沒有權限使用此指令。", color=error_color)
        私人訊息 = True
        await ctx.respond(embed=embed, ephemeral=私人訊息)


load_dotenv(dotenv_path=os.path.join(base_dir, "TOKEN.env"))
TOKEN = str(os.getenv("TOKEN"))
bot.run(TOKEN)
