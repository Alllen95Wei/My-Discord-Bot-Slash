def check_size(folder_path="C:\\MusicBot\\audio_cache"):
    # 匯入模組
    import os
    # 取得資料夾大小
    total_size = 0
    for path, dirs, files in os.walk(folder_path):
        for f in files:
            fp = os.path.join(path, f)
            total_size += os.stat(fp).st_size
    total_size = round(total_size / 10**7) / 100
    msg = "`\"" + folder_path + "\"` 大小： " + str(total_size) + " GB。"
    return msg
