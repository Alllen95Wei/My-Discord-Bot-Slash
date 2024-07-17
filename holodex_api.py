# coding:utf-8
import requests


BASE_URL = "https://holodex.net/api/v2"


class HolodexClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {"X-APIKEY": ""}

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
