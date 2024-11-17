# coding=utf-8
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import json
import requests
import logging


class YouTubeUploader:
    def __init__(self, file_path: str, title: str, description: str):
        self.video_id = None
        self.credentials = None
        self.file_path = file_path
        self.body = {
            "snippet": {
                "title": title,
                "description": description,
                "categoryId": "22",
            },
            "status": {"privacyStatus": "unlisted", "selfDeclaredMadeForKids": False},
        }
        self.credentials: Credentials
        self.video_id: str

    @staticmethod
    def refresh_token_is_valid(refresh_token: str) -> bool:
        result = requests.get(
            "https://www.googleapis.com/oauth2/v1/tokeninfo?access_token="
            + refresh_token,
            timeout=10,
        )
        return result.status_code == 200

    def setup_credentials(self, refresh_token: str = None):
        with open("google_client_secret.json", "r", encoding="utf-8") as f:
            secret_dict = json.load(f)
        if refresh_token is None:
            try:
                refresh_token = secret_dict["refresh_token"]
            except KeyError:
                raise Exception(
                    """
                \"refresh_token\" not found in \"google_client_secret.json\".
                https://accounts.google.com/o/oauth2/v2/auth/oauthchooseaccount?scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fyoutube.upload&response_type=token&redirect_uri=https%3A%2F%2Falllen95wei.github.io%2F&client_id=301053688733-0oighbmuqurd094jd9ttlb8ouoa4vjrp.apps.googleusercontent.com&service=lso&o2v=2&ddm=0&flowName=GeneralOAuthFlow
                """
                )
        elif not self.refresh_token_is_valid(refresh_token):
            raise Exception(
                """
            Refresh token has expired or invalid.
            https://accounts.google.com/o/oauth2/v2/auth/oauthchooseaccount?scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fyoutube.upload&response_type=token&redirect_uri=https%3A%2F%2Falllen95wei.github.io%2F&client_id=301053688733-0oighbmuqurd094jd9ttlb8ouoa4vjrp.apps.googleusercontent.com&service=lso&o2v=2&ddm=0&flowName=GeneralOAuthFlow
            """
            )
        self.credentials = Credentials(
            client_id=secret_dict["web"]["client_id"],
            quota_project_id=secret_dict["web"]["project_id"],
            token_uri=secret_dict["web"]["token_uri"],
            client_secret=secret_dict["web"]["client_secret"],
            token=secret_dict["token"],
            refresh_token=refresh_token,
        )

    def upload_video(self) -> dict:
        if self.credentials is None:
            raise RuntimeError(
                'Credentials not set. Run "setup_credentials" before uploading.'
            )
        else:
            youtube = build("youtube", "v3", credentials=self.credentials)

            # Docs: https://developers.google.com/youtube/v3/docs/videos/insert
            insert_request = youtube.videos().insert(
                part=",".join(self.body.keys()),
                body=self.body,
                media_body=MediaFileUpload(
                    filename=self.file_path, chunksize=-1, resumable=True
                ),
            )

            response = None
            while response is None:
                status, response = insert_request.next_chunk()
                if response is not None:
                    if "id" in response:
                        self.video_id = response["id"]
                        logging.info(
                            "Video id '%s' was successfully uploaded." % response["id"]
                        )
                        return response

    def upload_thumbnail(self, file_path: str) -> dict:
        if self.credentials is None:
            raise RuntimeError(
                'Credentials not set. Run "setup_credentials" before uploading.'
            )
        else:
            youtube = build("youtube", "v3", credentials=self.credentials)

            # Docs: https://developers.google.com/youtube/v3/docs/thumbnails/set
            insert_request = youtube.thumbnails().set(
                videoId=self.video_id,
                media_body=MediaFileUpload(
                    filename=file_path, chunksize=-1, resumable=True
                ),
            )

            response = None
            while response is None:
                status, response = insert_request.next_chunk()
                if response is not None:
                    return response


if __name__ == "__main__":
    # uploader = YouTubeUploader(
    #     file_path="test.mp4", title="Test Title", description="Test Description"
    # )
    # uploader.setup_credentials(input("貼上Refresh Token: "))
    # upload_result = uploader.upload()
    print(YouTubeUploader.refresh_token_is_valid(input("貼上Refresh Token: ")))
