def webm_to_mp3(file_name, mp3_file_path):
    import os

    print(mp3_file_path)
    command = "ffmpeg -i \"" + file_name + ".m4a\"" + " -vn -ab 160k -ar 44100 -y \"" + mp3_file_path + "\""
    print(command)
    os.system(command)
    os.remove(file_name + ".m4a")


if __name__ == "__main__":
    file_name = input("貼上要轉換檔案的路徑及名稱(不含附檔名)：")
    mp3_file_path = "\"" + input("輸入mp3檔輸出的路徑：") + file_name + ".mp3\""
    webm_to_mp3(file_name, mp3_file_path)
