# coding:utf-8
from dotenv import load_dotenv
import os
import requests


base_dir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(dotenv_path=os.path.join(base_dir, "TOKEN.env"))

BASE_URL = "https://holodex.net/api/v2"


class HolodexClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {"X-APIKEY": str(os.getenv("HOLODEX_TOKEN"))}

    def get_video_info(self, video_id: str) -> dict:
        url = f"{BASE_URL}/videos/{video_id}?lang=zh&c=1"
        result = self.session.get(url=url).json()
        return result

    def fetch_video_timeline(self, video_id: str) -> list[dict] | None:
        full_info = self.get_video_info(video_id)
        if "songs" in full_info and len(full_info["songs"]) > 0:
            return full_info["songs"]
        else:
            return None


if __name__ == "__main__":
    client = HolodexClient()
    vid = "UV9hqvqiM9c"
    print(client.fetch_video_timeline(vid))
