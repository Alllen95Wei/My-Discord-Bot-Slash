# coding=utf-8
import subprocess
import git
from time import sleep

REPO = git.Repo()


def update(pid, os):
    get_update_files()
    sleep(5)
    restart_running_bot(pid, os)


def get_update_files():
    # subprocess.run(["git", "fetch", "--all"])
    for remote in REPO.remotes:
        remote.fetch()
    subprocess.run(['git', 'reset', '--hard', 'origin/main'])
    REPO.remotes[0].pull()


def restart_running_bot(pid, os):
    subprocess.Popen("python main.py", creationflags=subprocess.CREATE_NEW_CONSOLE)
    kill_running_bot(pid, os)


def kill_running_bot(pid, os):
    if os == "Windows":
        subprocess.run(['taskkill', '/f', '/PID', str(format(pid))])
    elif os == "Linux":
        subprocess.run(['kill', '-9', str(format(pid))])


if __name__ == '__main__':
    get_update_files()
    print("已經嘗試取得更新檔案，請手動重啟機器人。")
    sleep(10)
