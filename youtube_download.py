# coding=utf-8
import yt_dlp as youtube_dl
import os

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


class Video:
    def __init__(self, url):
        self.url = url
        self.full_info = self.get_full_info(url)

    def download(self, file_name):
        dl_opts = {
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
        with youtube_dl.YoutubeDL(dl_opts) as ydl:
            return ydl.download([self.url])

    def get_id(self):
        info_dict = self.full_info
        vid = info_dict["id"]
        return vid

    def get_length(self):
        # get video length in seconds
        info_dict = self.full_info
        duration = info_dict["duration"]
        return duration

    def get_thumbnail(self):
        # get thumbnail url
        info_dict = self.full_info
        thumbnail = info_dict["thumbnail"]
        return thumbnail

    def get_title(self):
        # get video title
        info_dict = self.full_info
        title = info_dict["title"]
        return title

    def get_uploader(self):
        info_dict = self.full_info
        uploader = info_dict["uploader"]
        return uploader

    @staticmethod
    def get_full_info(url):
        # get full info
        with youtube_dl.YoutubeDL(ytdl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            return info_dict


if __name__ == "__main__":
    # youtube_download(url=input("請貼上要下載的連結："), file_name=input("請輸入下載後的檔案名稱："))
    print(Video.get_full_info(url=input("請貼上要下載的連結：")))
