import yt_dlp as youtube_dl
import os
from subprocess import run
from platform import system
from shlex import split


def youtube_download(url, file_name):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join("ytdl", file_name),
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'logtostderr': False,
        'default_search': 'auto',
        'usenetrc': False,
        "fixup": "detect_or_warn"
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        return ydl.download([url])


def get_id(url):
    if system() == "Windows":
        cmd = f"yt-dlp --skip-download --print \"%(id)s\" {url}"
    else:
        cmd = f"./yt-dlp --skip-download --print \"%(id)s\" {url}"

    vid = str(run(split(cmd), capture_output=True, text=True).stdout)
    return vid.replace("\n", "")


def get_length(url):
    # get video length in seconds
    ytdl_opts = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "nocheckcertificate": True,
        "restrictfilenames": True,
        "noplaylist": True,
        "logtostderr": False,
        "default_search": "auto",
        "usenetrc": False,
        "fixup": "detect_or_warn"
    }
    with youtube_dl.YoutubeDL(ytdl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        duration = info_dict["duration"]
        return duration


if __name__ == "__main__":
    # youtube_download(url=input("請貼上要下載的連結："), file_name=input("請輸入下載後的檔案名稱："))
    print(get_length(input("請貼上連結：")))
