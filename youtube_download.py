def youtube_download(url, file_name):
    import youtube_dl

    ydl_opts = {
        'format': 'bestaudio',
        'outtmpl': file_name,
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


if __name__ == "__main__":
    youtube_download(url=input("請貼上要下載的連結："), file_name=input("請輸入下載後的檔案名稱："))
