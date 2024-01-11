import youtube_download as yt_dl
import m4a_to_mp3 as mt3


def main_dl(video_instance: yt_dl.Video, file_name, mp3_path, bit_rate=128):
    video_instance.download(file_name + ".m4a")
    mt3.m4a_to_mp3(file_name, mp3_path, bit_rate)
    return "finished"


if __name__ == "__main__":
    url = input("請貼上要下載的連結：")
    m_file_name = input("請輸入下載後的檔案名稱(不含副檔名)：")
    m_mp3_path = input("輸入mp3檔輸出的路徑(結尾請加\\)：") + m_file_name + ".mp3"
    main_dl(yt_dl.Video(url), m_file_name, m_mp3_path, 320)
