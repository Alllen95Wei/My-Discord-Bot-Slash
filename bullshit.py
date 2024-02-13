# coding=utf-8
import requests


def bullshit(topic: str, length: int) -> str:
    url = "https://api.howtobullshit.me/bullshit"
    payload = {"Topic": topic, "MinLen": length}
    r = requests.get(url, json=payload, headers={"Content-Type": "application/json; charset=utf-8"}, timeout=10)
    r = r.text.replace(u"&nbsp;", u"")
    r = r.replace(u"<br><br>", "\n")
    return r


if __name__ == "__main__":
    print(bullshit("網路爬蟲", 2000))
