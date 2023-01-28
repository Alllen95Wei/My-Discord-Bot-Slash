def main_dl(url, file_name, mp3_path):
    import youtube_download as yt_dl
    import m4a_to_mp3 as mt3

    yt_dl.youtube_download(url, file_name + ".m4a")
    mt3.webm_to_mp3(file_name, mp3_path)
    return "finished"


if __name__ == "__main__":
    url = input("請貼上要下載的連結：")
    file_name = input("請輸入下載後的檔案名稱(不含副檔名)：")
    mp3_path = "\"" + input("輸入mp3檔輸出的路徑(結尾請加\\)：") + file_name + ".mp3\""
    main_dl(url, file_name, mp3_path)
