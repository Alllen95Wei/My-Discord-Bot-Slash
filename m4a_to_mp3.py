# coding=utf-8
import os


def m4a_to_mp3(mp3_file_path, bit_rate=128):
    input_file_path = mp3_file_path.replace(".mp3", ".m4a")
    command = f"ffmpeg -i \"{input_file_path}\" -vn -ab {bit_rate}k -ar 44100 -y \"{mp3_file_path}\""
    os.system(command)
    os.remove(input_file_path)
    return mp3_file_path


if __name__ == "__main__":
    f_name = input("貼上要轉換檔案的路徑及名稱(不含附檔名)：")
    path = "\"" + input("輸入mp3檔輸出的路徑：") + f_name + ".mp3\""
    m4a_to_mp3(path)
