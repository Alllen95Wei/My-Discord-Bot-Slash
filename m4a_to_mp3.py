import os


def m4a_to_mp3(file_name, mp3_file_path, bit_rate=128):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    input_file_path = os.path.join(base_dir, "ytdl", file_name + ".m4a")
    output_file_path = os.path.join(base_dir, "ytdl", mp3_file_path)
    command = f"ffmpeg -i \"{input_file_path}\" -vn -ab {bit_rate}k -ar 44100 -y \"{output_file_path}\""
    os.system(command)
    os.remove(f"{input_file_path}")


if __name__ == "__main__":
    f_name = input("貼上要轉換檔案的路徑及名稱(不含附檔名)：")
    mp3_file_path = "\"" + input("輸入mp3檔輸出的路徑：") + f_name + ".mp3\""
    m4a_to_mp3(f_name, mp3_file_path)
