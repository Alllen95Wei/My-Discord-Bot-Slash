# coding=utf-8
import PIL
import mutagen.id3
from mutagen.id3 import ID3
import requests
from PIL import Image
import io
from string import hexdigits
from random import choice
from os import remove, path
# import magic
import logging

import youtube_download as yt_dl
import m4a_to_mp3 as mt3


def main_dl(
    video_instance: yt_dl.Video,
    mp3_path,
    metadata: dict,
    section: list = None,
    bit_rate=128,
):
    if not path.exists(mp3_path):
        if section is None:
            section = [0, 0]
        if section == [0, 0]:
            video_instance.download(mp3_path.replace(".mp3", ".m4a"))
        else:
            video_instance.download_section(mp3_path.replace(".mp3", ".m4a"), section[0], section[1])
        mt3.m4a_to_mp3(mp3_path, bit_rate)
    clear_mp3_metadata(mp3_path)
    edit_mp3_metadata(mp3_path, metadata) if metadata != {} else None
    return "finished"


def edit_mp3_metadata(mp3_path: str, data: dict):
    audio_file = ID3(mp3_path, v2_version=3)
    audio_file.add(
        mutagen.id3.TIT2(encoding=3, text=data["title"] if data["title"] else "")
    )
    audio_file.add(
        mutagen.id3.TPE1(encoding=3, text=data["artist"] if data["artist"] else "")
    )
    if "thumbnail_url" in data and data["thumbnail_url"] != "":
        try:
            img_name = save_thumbnail_from_url(data["thumbnail_url"])
            with open(img_name, "rb") as f:
                image_data = f.read()
            remove(img_name)
            audio_file.add(
                mutagen.id3.APIC(encoding=3, mime="image/png", type=3, data=image_data)
            )
        except Exception as e:
            logging.warning(f"加入縮圖時發生錯誤，已取消 ({e})")
    audio_file.save(v2_version=3)


def clear_mp3_metadata(mp3_path: str):
    audio_file = ID3(mp3_path, v2_version=3)
    audio_file.delete()
    audio_file.save(v2_version=3)


def save_thumbnail_from_url(url: str):
    image_data = requests.get(url, timeout=10).content
    try:
        image = Image.open(io.BytesIO(image_data)).convert("RGB")
    except PIL.UnidentifiedImageError as e:
        raise RuntimeError("Invalid thumbnail URL!") from e
    random_char_list = [choice(hexdigits) for _ in range(4)]
    file_name = "".join(random_char_list) + ".png"
    image.save(file_name)
    return file_name


if __name__ == "__main__":
    dl_url = input("請貼上要下載的連結：")
    m_mp3_path = input("輸入mp3檔輸出的路徑(結尾須為.mp3)：")
    main_dl(
        yt_dl.Video(dl_url),
        m_mp3_path,
        {
            "title": "test1",
            "artist": "浠Mizuki",
            "thumbnail_url": "https://www.youtube.com/",
        },
        bit_rate=320,
    )
