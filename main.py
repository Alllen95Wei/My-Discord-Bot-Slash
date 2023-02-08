# coding: utf-8
import discord
from discord.ext import commands
from discord.ext import tasks
from discord import Option
import git
import os
import time
from dotenv import load_dotenv
from random import choice
from random import randint
from shlex import split
from subprocess import run
from platform import system

import check_folder_size
from youtube_to_mp3 import main_dl
import detect_pc_status
import update as upd
import user_exp

intents = discord.Intents.all()
bot = commands.Bot(intents=intents, help_command=None)
base_dir = os.path.abspath(os.path.dirname(__file__))
default_color = 0x5FE1EA
error_color = 0xF1411C
# 載入TOKEN
load_dotenv(dotenv_path=os.path.join(base_dir, "TOKEN.env"))
TOKEN = str(os.getenv("TOKEN"))


@tasks.loop(seconds=10)
async def give_voice_exp():  # 給予語音經驗
    voice_channel_lists = []
    for server in bot.guilds:
        for channel in server.channels:
            if channel.type == discord.ChannelType.voice:
                voice_channel_lists.append(channel)
                members = channel.members
                for member in members:
                    if not member.bot and not member.voice.self_deaf:
                        if member.voice.self_mute:
                            user_exp.add_exp(member.id, "voice", 0.5)
                        else:
                            user_exp.add_exp(member.id, "voice", 1)
                        if user_exp.level_calc(member.id, "voice"):
                            embed = discord.Embed(title="等級提升",
                                                  description=f"恭喜 <@{member.id}> *語音*等級升級到 "
                                                              f"**{user_exp.get_level(member.id, 'text')}** 等！",
                                                  color=default_color)
                            embed.set_thumbnail(url=member.display_avatar)
                            await member.send(embed=embed)


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
async def on_member_join(member):
    embed = discord.Embed(title="歡迎新成員！", description=f"歡迎{member.mention}加入**{member.guild}**！",
                          color=0x16D863)
    join_date = member.joined_at.strftime("%Y-%m-%d %H:%M:%S")
    embed.set_footer(text=f"於 {join_date} 加入")
    await member.guild.system_channel.send(embed=embed)
    user_exp.set_join_date(member.id, join_date)
    new_member = await bot.fetch_user(member.id)
    embed = discord.Embed(
        title=f"歡迎加入 {member.guild.name} ！",
        description="請到[這裡](https://discord.com/channels/857996539262402570/858373026960637962)查看頻道介紹。",
        color=0x57c2ea)
    await new_member.send(embed=embed)
    embed = discord.Embed(
        title="在開始之前...",
        description="什麼頻道都沒看到嗎？這是因為你**並未被分配身分組**。但是放心，我們會盡快確認你的身分，到時你就能加入我們了！",
        color=0x57c2ea)
    await new_member.send(embed=embed)


@bot.event
async def on_member_update(before, after):
    server_list = []
    for server in bot.guilds:
        server_list.append(server)
    only_server = server_list[0]
    new_roles_list = {}
    embed = discord.Embed(title="獲得了新身分組！", description="你獲得了下列新的身分組！", color=default_color)
    if before.roles == after.roles:
        return
    normal_role = discord.utils.get(only_server.roles, id=858365679102328872)
    if normal_role in after.roles:
        if normal_role not in before.roles:
            new_roles_list["旁觀者"] = "「貓娘實驗室」中的最基本身分組。\n" \
                                      "取得此身分組後，可以存取大多數頻道。"
    GAMER = discord.utils.get(only_server.roles, id=993094175484559441)
    if GAMER in after.roles:
        if GAMER not in before.roles:
            new_roles_list["GAMER"] = "「貓娘實驗室」中，遊戲玩家們專用的身分組。\n" \
                                      "你現在可以存取「遊戲討論」的所有頻道！"
    VIEWER = discord.utils.get(only_server.roles, id=1066721427862077571)
    if VIEWER in after.roles:
        if VIEWER not in before.roles:
            new_roles_list["VIEWER"] = "「貓娘實驗室」中，遊戲觀眾的身分組。\n" \
                                       "現在起，當有玩家選擇在「遊戲討論」的語音頻道中直播，你將能參與觀看！"
    one_o_four = discord.utils.get(only_server.roles, id=1060075117822083163)
    if one_o_four in after.roles:
        if one_o_four not in before.roles:
            new_roles_list["104"] = "「貓娘實驗室」中，104班同學們的專用身分組。\n" \
                                    "你可以加入104班的專屬頻道，跟大家參與討論。"
    for i in new_roles_list:
        embed.add_field(name=i, value=new_roles_list[i], inline=False)
    embed.set_footer(text="如果你認為被意外分配到錯誤的身分組，請聯絡管理員。")
    await after.send(embed=embed)


@bot.event
async def on_member_remove(member):
    embed = discord.Embed(title="有人離開了我們...", description=f"{member.name} 離開了 **{member.guild}** ...",
                          color=0x095997)
    leave_date = time.strftime("%Y-%m-%d %H:%M:%S")
    embed.set_footer(text=f"於 {leave_date} 離開")
    await member.guild.system_channel.send(embed=embed)


@bot.event
async def on_ready():
    print("機器人準備完成！")
    print(f"PING值：{round(bot.latency * 1000)}ms")
    print(f"登入身分：{bot.user.name}#{bot.user.discriminator}")
    status = discord.Activity(name="斜線指令 參戰！", type=discord.ActivityType.playing)
    await bot.change_presence(activity=status, status=discord.Status.online)
    await check_voice_channel()
    for guild in bot.guilds:
        for member in guild.members:
            join_at_list = [member.joined_at.year, member.joined_at.month, member.joined_at.day,
                            member.joined_at.hour, member.joined_at.minute, member.joined_at.second]
            print(f"{member.name}: {join_at_list}")
            user_exp.set_join_date(member.id, join_at_list)
    await give_voice_exp.start()


@bot.slash_command(name="help", description="提供指令協助。")
async def help(ctx,
               私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):
    embed = discord.Embed(title="指令協助", color=default_color)
    embed.add_field(name="</help:1069235277433942057>", value="提供指令協助。", inline=False)
    embed.add_field(name="</about:1070988511961948181>", value="提供關於這隻機器人的資訊。", inline=False)
    embed.add_field(name="</ping:1069046879473647637>", value="查詢機器人PING值(ms)。", inline=False)
    embed.add_field(name="</ama:1059105845629165568>", value="就是8號球，給你這個問題的隨機回答。", inline=False)
    embed.add_field(name="</random:1059754228882616360>", value="在指定數字範圍隨機取得一數，不指定範圍則設為1~100。",
                    inline=False)
    embed.add_field(name="</qrcode:1063349408223207516>", value="將輸入的文字轉為QR Code。", inline=False)
    embed.add_field(name="</sizecheck:1068693011858456656>", value="檢查`C:\\MusicBot\\audio_cache`的大小。",
                    inline=False)
    embed.add_field(name="</ytdl:1068693011858456657>",
                    value="將YouTube影片下載為mp3。由於Discord有檔案大小限制，因此有時可能會失敗。",
                    inline=False)
    embed.add_field(name="</user_info:1071752534638735440>", value="取得使用者的資訊。", inline=False)
    embed.add_field(name="</rc:1068693011858456658>", value="重新連接至語音頻道。可指定頻道，否則將自動檢測<@885723595626676264>"
                                                            "及<@657519721138094080>在哪個頻道並加入。", inline=False)
    embed.add_field(name="</dc:1069046879473647636>", value="從目前的語音頻道中斷連接。", inline=False)
    embed.add_field(name="</dps:1068693011858456659>", value="查詢伺服器電腦的CPU及記憶體使用率。", inline=False)
    embed.add_field(name="</cmd:1069046879473647638>", value="在伺服器端執行指令並傳回結果。", inline=False)
    embed.add_field(name="</update:1069046879473647639>", value="更新機器人。", inline=False)
    await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="about", description="提供關於這隻機器人的資訊。")
async def about(ctx,
                私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):
    embed = discord.Embed(title="關於", color=default_color)
    embed.set_thumbnail(url=bot.user.display_avatar)
    embed.add_field(name="程式碼與授權", value="本機器人由<@657519721138094080>維護，使用[Py-cord]"
                    "(https://github.com/Pycord-Development/pycord)進行開發。\n"
                    "本機器人的程式碼及檔案皆可在[這裡](https://github.com/Alllen95Wei/My-Discord-Bot-Slash)查看。",
                    inline=True)
    embed.add_field(name="聯絡", value="如果有任何技術問題及建議，請聯絡<@657519721138094080>。", inline=True)
    repo = git.Repo(search_parent_directories=True)
    sha = repo.head.object.hexsha
    year = time.strftime("%Y")
    embed.set_footer(text=f"©Allen Why, {year} | 版本：commit {sha[:7]}")
    await ctx.respond(embed=embed, ephemeral=私人訊息)


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
        ball_result1 = "🟢"
    elif ball_result1 == "s":
        ball_result2 = choice(ans_s)
        ball_result1 = "🟡"
    else:
        ball_result2 = choice(ans_b)
        ball_result1 = "🔴"
    embed = discord.Embed(title="8號球", description=f"你的問題：{問題}", color=default_color)
    embed.add_field(name="回答", value=f"{ball_result1}\"{ball_result2}\"", inline=False)
    await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="random", description="在指定數字範圍隨機取得一數，不指定範圍則設為1~100。")
async def random(ctx,
                 range_min: Option(name="min", description="最小值", required=False, input_type=int) = 0,
                 range_max: Option(name="max", description="最大值", required=False, input_type=int) = 100,
                 私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):
    ans = randint(int(range_min), int(range_max))
    embed = discord.Embed(title="隨機", description=f"數字範圍：{range_min}~{range_max}", color=default_color)
    embed.add_field(name="結果", value=f"`{ans}`", inline=False)
    await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="qrcode", description="將輸入的文字轉為QR Code。")
async def qrcode(ctx,
                 內容: Option(str, "要轉換的文字", required=True),
                 私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):
    import urllib.parse
    text = urllib.parse.quote(內容)
    url = f"https://chart.apis.google.com/chart?cht=qr&chs=500x500&choe=UTF-8&chld=H|1&chl={text}"
    embed = discord.Embed(title="QR Code", description=f"內容：{內容}", color=default_color)
    embed.set_image(url=url)
    await ctx.respond(embed=embed, ephemeral=私人訊息)


user_info = bot.create_group(name="user_info", description="使用者的資訊、經驗值等。")


@user_info.command(name="show", description="顯示使用者的資訊。")
async def show(ctx,
               使用者: Option(discord.Member, "要查詢的使用者", required=False) = None,
               私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):
    if 使用者 is None:
        使用者 = ctx.author
    text_exp = user_exp.get_exp(使用者.id, "text")
    text_level = user_exp.get_level(使用者.id, "text")
    voice_exp = user_exp.get_exp(使用者.id, "voice")
    voice_level = user_exp.get_level(使用者.id, "voice")
    avatar = 使用者.display_avatar
    embed = discord.Embed(title="經驗值", description=f"使用者：{使用者.mention}的經驗值", color=default_color)
    embed.add_field(name="文字等級", value=f"{text_level}", inline=True)
    embed.add_field(name="文字經驗值", value=f"{text_exp}", inline=True)
    embed.add_field(name="語音等級", value=f"{voice_level}", inline=False)
    embed.add_field(name="語音經驗值", value=f"{voice_exp}", inline=True)
    date = user_exp.get_join_date_in_str(使用者.id)
    embed.add_field(name="加入時間", value=f"{date}", inline=False)
    joined_date = user_exp.joined_time(使用者.id)
    embed.add_field(name="已加入", value=f"{joined_date}", inline=False)
    embed.set_thumbnail(url=avatar)
    await ctx.respond(embed=embed, ephemeral=私人訊息)


edit = user_info.create_subgroup(name="edit", description="編輯使用者的資訊。")


# TODO: 解決參數丟失問題
@edit.command(name="exp", description="編輯使用者的經驗值。")
async def exp(ctx,
              使用者: Option(discord.Member, "要編輯的使用者", required=True),
              類型: Option(str, "要編輯的經驗值類型", required=True, choices=["text", "voice"]),
              經驗值: Option(int, "要編輯的經驗值數量，若要扣除則輸入負值", required=True),
              私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):
    if ctx.author == bot.get_user(657519721138094080):
        before_exp = user_exp.get_exp(使用者.id, 類型)
        user_exp.add_exp(使用者.id, 類型, 經驗值)
        after_exp = user_exp.get_exp(使用者.id, 類型)
        embed = discord.Embed(title="編輯經驗值", description=f"已編輯{使用者.mention}的**{類型}**經驗值。",
                              color=default_color)
        embed.add_field(name="編輯前", value=before_exp, inline=True)
        if 經驗值 > 0:
            embed.add_field(name="➡️增加", value=f"*{經驗值}*", inline=True)
        else:
            embed.add_field(name="減少", value=f"*{abs(經驗值)}*", inline=True)
        embed.add_field(name="編輯後", value=after_exp, inline=True)
        await ctx.respond(embed=embed, ephemeral=私人訊息)
    else:
        embed = discord.Embed(title="錯誤", description="你沒有權限使用這個指令。", color=error_color)
        await ctx.respond(embed=embed, ephemeral=私人訊息)


@edit.command(name="lvl", description="編輯使用者的等級。")
async def lvl(ctx,
              使用者: Option(discord.Member, "要編輯的使用者", required=True),
              類型: Option(str, "要編輯的等級類型", required=True, choices=["text", "voice"]),
              等級: Option(int, "要編輯的等級數量，若要扣除則輸入負值", required=True),
              私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):
    if ctx.author == bot.get_user(657519721138094080):
        before_lvl = user_exp.get_level(使用者.id, 類型)
        user_exp.add_level(使用者.id, 類型, 等級)
        after_lvl = user_exp.get_level(使用者.id, 類型)
        embed = discord.Embed(title="編輯經驗值", description=f"已編輯{使用者.mention}的**{類型}**等級。",
                              color=default_color)
        embed.add_field(name="編輯前", value=before_lvl, inline=True)
        if 等級 > 0:
            embed.add_field(name="增加", value=f"*{等級}*", inline=True)
        else:
            embed.add_field(name="減少", value=abs(等級), inline=True)
        embed.add_field(name="編輯後", value=after_lvl, inline=True)
        await ctx.respond(embed=embed, ephemeral=私人訊息)
    else:
        embed = discord.Embed(title="錯誤", description="你沒有權限使用這個指令。", color=error_color)
        await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="sizecheck", description="檢查\"C:\\MusicBot\\audio_cache\"的大小。")
async def sizecheck(ctx,
                    私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):
    size = check_folder_size.check_size()
    embed = discord.Embed(title="資料夾大小", description=size, color=default_color)
    await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="ytdl", description="將YouTube影片下載為mp3。由於Discord有"
                                            "檔案大小限制，因此有時可能會失敗。")
async def ytdl(ctx,
               連結: Option(str, "欲下載的YouTube影片網址", required=True),
               私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):
    await ctx.defer()
    file_name = str(ctx.author) + 連結[-11:]
    if main_dl(連結, file_name, file_name + ".mp3") == "finished":
        try:
            await ctx.respond(file=discord.File(file_name + ".mp3"), ephemeral=私人訊息)
            os.remove(file_name + ".mp3")
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
            embed = discord.Embed(title="已加入頻道", description=f"已經自動加入了 <#{msg}>！", color=default_color)
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
    embed.add_field(name="記憶體使用率", value=f"{detect_pc_status.get_ram_usage_detail()}")
    await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="ping", description="查詢機器人PING值(ms)。")
async def ping(ctx,
               私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):
    embed = discord.Embed(title="PONG!✨", color=default_color)
    embed.add_field(name="PING值", value=f"`{round(bot.latency * 1000)}` ms")
    await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="restart", description="重啟機器人。")
async def restart(ctx,
                  私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):
    if ctx.author == bot.get_user(657519721138094080):
        embed = discord.Embed(title="機器人重啟中", description="機器人正在重啟中。", color=default_color)
        await ctx.respond(embed=embed, ephemeral=私人訊息)
        event = discord.Activity(type=discord.ActivityType.playing, name="重啟中...")
        await bot.change_presence(status=discord.Status.do_not_disturb, activity=event)
        upd.restart_running_bot(os.getpid(), system())
    else:
        embed = discord.Embed(title="錯誤", description="你沒有權限使用這個指令。", color=error_color)
        await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.slash_command(name="cmd", description="在伺服器端執行指令並傳回結果。")
async def cmd(ctx,
              指令: Option(str, "要執行的指令", required=True),
              私人訊息: Option(bool, "是否以私人訊息回應", required=False) = False):
    if ctx.author == bot.get_user(657519721138094080):
        try:
            await ctx.defer()
            command = split(指令)
            if command[0] == "cmd":
                embed = discord.Embed(title="錯誤", description="基於安全原因，你不能執行這個指令。", color=error_color)
                await ctx.respond(embed=embed, ephemeral=私人訊息)
                return
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
        upd.update(os.getpid(), system())
    else:
        embed = discord.Embed(title="錯誤", description="你沒有權限使用此指令。", color=error_color)
        私人訊息 = True
        await ctx.respond(embed=embed, ephemeral=私人訊息)


@bot.event
async def on_message(message):
    msg_in = message.content
    exclude_channel = [1035754607286169631, 1035754607286169631, 891665312028713001]
    if message.channel.id == 891665312028713001:
        if msg_in.startswith("https://www.youtube.com") or msg_in.startswith("https://youtu.be") or \
                msg_in.startswith("https://open.spotify.com"):
            if "&list=" in msg_in:
                msg_in = msg_in[:msg_in.find("&list=")]
                await message.channel.send(f"<@{message.author.id}> 偵測到此連結來自播放清單！已轉換為單一影片連結。")
            ap_cmd = "ap!p " + msg_in
            await message.channel.send(ap_cmd)
            return
    if message.channel.id in exclude_channel:
        return
    if not message.author.bot and isinstance(msg_in, str):
        user_exp.add_exp(message.author.id, "text", len(msg_in))
    elif not message.author.bot and isinstance(msg_in, discord.File):
        user_exp.add_exp(message.author.id, "text", 1)
    if user_exp.level_calc(message.author.id, "text"):
        embed = discord.Embed(title="等級提升", description=f"恭喜 <@{message.author.id}> *文字*等級升級到 "
                              f"**{user_exp.get_level(message.author.id, 'text')}** 等！", color=default_color)
        embed.set_thumbnail(url=message.author.display_avatar)
        await message.channel.send(embed=embed)


bot.run(TOKEN)
