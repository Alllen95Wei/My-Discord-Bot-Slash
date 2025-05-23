# coding=utf-8
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

intents = discord.Intents.all()
bot = commands.Bot(intents=intents, help_command=None)


@bot.event
async def on_ready():
    print("機器人準備完成！指令已清除完畢。")
    print(f"PING值：{round(bot.latency * 1000)}ms")
    print(f"登入身分：{bot.user.name}#{bot.user.discriminator}")
    clean_user_data = input("刪除使用者資料？(Y/N)")
    if clean_user_data.lower() == "y":
        user_data_path = os.path.join(os.path.dirname(__file__), "user_data")
        for file in os.listdir(user_data_path):
            os.remove(os.path.join(user_data_path, file))
            print("刪除檔案：", file)
        ytdl_path = os.path.join(os.path.dirname(__file__), "ytdl")
        for file in os.listdir(ytdl_path):
            os.remove(os.path.join(ytdl_path, file))
            print("刪除檔案：", file)
        logs_path = os.path.join(os.path.dirname(__file__), "logs")
        for file in os.listdir(logs_path):
            os.remove(os.path.join(logs_path, file))
            print("刪除檔案：", file)
        soundboard_path = os.path.join(os.path.dirname(__file__), "soundboard_data")
        for file in os.listdir(logs_path):
            os.remove(os.path.join(soundboard_path, file))
            print("刪除檔案：", file)
        thumbnail_path = os.path.join(os.path.dirname(__file__), "thumbnails")
        for file in os.listdir(thumbnail_path):
            os.remove(os.path.join(thumbnail_path, file))
            print("刪除檔案：", file)
        cookies_path = os.path.join(os.path.dirname(__file__), "cookies")
        for file in os.listdir(cookies_path):
            os.remove(os.path.join(cookies_path, file))
            print("刪除檔案：", file)
        print("刪除完畢。")
    print("結束工作...")
    exit()

load_dotenv("TOKEN.env")
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
