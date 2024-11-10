# coding=utf-8
import random
import os
import cv2
from PIL import Image, ImageDraw, ImageFont


base_dir = os.path.abspath(os.path.dirname(__file__))


class ThumbnailGenerator:
    def __init__(self, image_source_path: str = None, video_source_path: str = None):
        if image_source_path is None and video_source_path is None:
            raise ValueError(
                "Either image_source_path or video_source_path should be str, not None"
            )
        self.video_path = video_source_path
        self.image_sources: list[str] = []
        if isinstance(image_source_path, str):
            self.image_sources.append(image_source_path)

    def extract_random_frames(self, count: int) -> list[str]:
        generated_frames = []
        for i in range(count):
            video = cv2.VideoCapture(self.video_path)
            frame_count = video.get(cv2.CAP_PROP_FRAME_COUNT)
            frame_no = random.randint(1, int(frame_count))
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
            success, image = video.read()
            if success:
                file_path = os.path.join(base_dir, f"frame_{frame_no}.jpg")
                cv2.imwrite(file_path, image)
                generated_frames.append(file_path)
        self.image_sources += generated_frames
        return generated_frames

    def write_title(self, title: str, color: int = None):
        for f in self.image_sources:
            img = Image.open(f)
            canva = ImageDraw.Draw(img)
            font_size = img.height * 0.2
            font = ImageFont.truetype(
                "/home/allen95wei/下載/Iansui-Regular.ttf", font_size
            )
            canva.text(
                xy=(img.width / 2, img.height),
                text=title,
                font=font,
                fill=(200, 0, 0),
                anchor="mb",
                align="center",
            )
            img.show()
            img.save(f)
            img.close()


if __name__ == "__main__":
    v_obj = ThumbnailGenerator("maxresdefault.jpg")
    # v_obj.extract_random_frames(5)
    v_obj.write_title(
        "test / 測試",
    )
