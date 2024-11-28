# coding=utf-8
import yt_dlp
import os
from moviepy import VideoFileClip, vfx
import uuid

base_dir = os.path.abspath(os.path.dirname(__file__))
DEFAULT_COOKIE_TXT_PATH = os.path.join(base_dir, "cookies.txt")
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
    "cookiefile": DEFAULT_COOKIE_TXT_PATH
    # "username": "oauth2",
    # "password": "",
}


class Video:
    def __init__(self, url: str, cookie_file_path: str = DEFAULT_COOKIE_TXT_PATH):
        self.url = url
        self.full_info = self.get_full_info(url)
        self.cookie_file_path = cookie_file_path if cookie_file_path else DEFAULT_COOKIE_TXT_PATH

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
            "cookiefile": self.cookie_file_path,
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
            "cookiefile": self.cookie_file_path,
            # "username": "oauth2",
            # "password": "",
        }
        with yt_dlp.YoutubeDL(dl_opts) as ydl:
            return ydl.download([self.url])

    def download_section_in_mp4(self, file_path: str, start_time: int, end_time: int, use_legacy: bool = False):
        if not use_legacy:
            dl_opts = {
                "merge_output_format": "mp4",
                "final_ext": "mp4",
                "format": "bestaudio+bestvideo/best",
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
                "cookiefile": self.cookie_file_path,
                # "username": "oauth2",
                # "password": "",
            }
            with yt_dlp.YoutubeDL(dl_opts) as ydl:
                return ydl.download([self.url])
        else:
            cached_file_name = "cache_" + self.get_id() + ".mp4"
            self.download_in_mp4(cached_file_name)
            v_obj = VideoEditor(cached_file_name)
            v_obj.clip(start_time, end_time)
            v_obj.save_video(file_path)
            os.remove(cached_file_name)

    def download_in_mp4(self, file_path: str):
        dl_opts = {
            "merge_output_format": "mp4",
            "final_ext": "mp4",
            "format": "bestaudio+bestvideo/best",
            "outtmpl": file_path,
            "restrictfilenames": True,
            "noplaylist": True,
            "nocheckcertificate": True,
            "logtostderr": False,
            "default_search": "auto",
            "usenetrc": False,
            "fixup": "detect_or_warn",
            "cookiefile": self.cookie_file_path,
            # "username": "oauth2",
            # "password": "",
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
        if info_dict.get("is_live", None) is None:
            return False
        return info_dict["is_live"]

    @staticmethod
    def get_full_info(url) -> dict:
        with yt_dlp.YoutubeDL(NO_DL_OPTS) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            if info_dict is None:
                raise RuntimeError("`get_full_info` failed. Are you blocked by YouTube?")
            return info_dict


class VideoEditor:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.clip_obj = VideoFileClip(file_path)

    def clip(self, start_time: float, end_time: float):
        self.clip_obj = self.clip_obj.subclipped(start_time, end_time)

    def fade(self, seconds: float, fade_in: bool = True, fade_out: bool = True):
        if fade_in:
            self.clip_obj = self.clip_obj.with_effects([vfx.FadeIn(seconds)])
        if fade_out:
            self.clip_obj = self.clip_obj.with_effects([vfx.FadeOut(seconds)])

    def save_video(self, destination_file_path: str = None):
        if destination_file_path is None:
            destination_file_path = self.file_path
        random_file_name = str(uuid.uuid4()).split("-")[-1] + ".mp4"
        self.clip_obj.write_videofile(random_file_name)
        self.clip_obj.close()
        os.replace(random_file_name, destination_file_path)


if __name__ == "__main__":
    # youtube_download(url=input("請貼上要下載的連結："), file_name=input("請輸入下載後的檔案名稱："))
    v = Video(url=input("請貼上要下載的連結："))
    v.download_section_in_mp4("test.mp4", 5, 10, True)
    editor = VideoEditor("test.mp4")
    editor.fade(0.5)
    editor.save_video()
