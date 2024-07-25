# coding=utf-8
import yt_dlp

NO_DL_OPTS = {
    "skip_download": True,
    "quiet": False,
    "no_warnings": True,
    "ignoreerrors": True,
    "nocheckcertificate": True,
    "restrictfilenames": True,
    "noplaylist": True,
    "logtostderr": False,
    "default_search": "auto",
    "usenetrc": False,
    "fixup": "detect_or_warn",
    "username": "oauth2",
    "password": "",
}


class Video:
    def __init__(self, url):
        self.url = url
        self.full_info = self.get_full_info(url)

    def download(self, file_path: str):
        dl_opts = {
            "format": "bestaudio/best",
            "outtmpl": file_path,
            "restrictfilenames": True,
            "noplaylist": True,
            "nocheckcertificate": True,
            "logtostderr": False,
            "default_search": "auto",
            "usenetrc": False,
            "fixup": "detect_or_warn",
            "username": "oauth2",
            "password": "",
        }
        with yt_dlp.YoutubeDL(dl_opts) as ydl:
            return ydl.download([self.url])

    def download_section(self, file_path: str, start_time: int, end_time: int):
        dl_opts = {
            "format": "bestaudio/best",
            "outtmpl": file_path,
            "restrictfilenames": True,
            "noplaylist": True,
            "nocheckcertificate": True,
            "logtostderr": False,
            "default_search": "auto",
            "usenetrc": False,
            "fixup": "detect_or_warn",
            "external_downloader": "ffmpeg",
            "external_downloader_args": {
                "ffmpeg_i": ["-ss", str(start_time), "-to", str(end_time)],
            },
            "username": "oauth2",
            "password": "",
        }
        with yt_dlp.YoutubeDL(dl_opts) as ydl:
            return ydl.download([self.url])

    def get_id(self):
        info_dict = self.full_info
        vid = info_dict["id"]
        return vid

    def get_length(self):
        info_dict = self.full_info
        duration = info_dict["duration"]
        return duration

    def get_thumbnail(self):
        info_dict = self.full_info
        thumbnail = info_dict["thumbnail"]
        return thumbnail

    def get_title(self):
        info_dict = self.full_info
        title = info_dict["title"]
        return title

    def get_uploader(self):
        info_dict = self.full_info
        uploader = info_dict["uploader"]
        return uploader

    def get_extractor(self):
        info_dict = self.full_info
        extractor = info_dict["extractor"]
        return extractor

    def is_live(self) -> bool:
        info_dict = self.full_info
        try:
            return info_dict["is_live"]
        except KeyError:
            return False

    @staticmethod
    def get_full_info(url):
        with yt_dlp.YoutubeDL(NO_DL_OPTS) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            return info_dict


if __name__ == "__main__":
    # youtube_download(url=input("請貼上要下載的連結："), file_name=input("請輸入下載後的檔案名稱："))
    v = Video(url=input("請貼上要下載的連結："))
    v.download_section("test.wav", 0, 10)
