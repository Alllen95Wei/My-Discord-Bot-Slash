# coding=utf-8
import random
import os
from pathlib import Path
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageColor
from uuid import uuid4
from time import time


base_dir = os.path.abspath(os.path.dirname(__file__))


class ThumbnailGenerator:
    def __init__(self, image_source_path: str = None, video_source_path: str = None):
        self.uuid: str = str(uuid4())
        if image_source_path is None and video_source_path is None:
            raise ValueError(
                "Either image_source_path or video_source_path should not be None"
            )
        self.video_path: str = video_source_path
        self.image_sources: list[str] = []
        if isinstance(image_source_path, str):
            self.image_sources.append(image_source_path)

        self.canvases: dict[str, tuple[Image, ImageDraw]] = {}

    @staticmethod
    def upscale_to_1080p(img: Image) -> Image:
        upscale_ratio = 1920 / img.width
        img = img.resize(
            (int(img.width * upscale_ratio), int(img.height * upscale_ratio)),
            Image.Resampling.BOX,
        )
        return img

    def load_images_to_canvases(self):
        for f in self.image_sources:
            img = self.upscale_to_1080p(Image.open(f))
            canvas = ImageDraw.Draw(img)
            self.canvases[f] = (img, canvas)

    def save_canvases(self, folder: str = "thumbnails") -> list[str]:
        output_files = []
        output_dir = os.path.join(base_dir, folder)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        for f in self.canvases:
            img, canvas = self.canvases[f]
            file_path = os.path.join(output_dir, Path(f).name)
            img.save(file_path)
            img.close()
            output_files.append(file_path)
        return output_files

    def extract_random_frames(self, count: int) -> list[str]:
        generated_frames = []
        video = cv2.VideoCapture(self.video_path)
        frame_count = video.get(cv2.CAP_PROP_FRAME_COUNT)
        for i in range(count):
            frame_no = random.randint(1, int(frame_count))
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
            success, image = video.read()
            if success:
                file_path = os.path.join(base_dir, "thumbnails", f"{self.uuid.split('-')[-1]}_{frame_no}.jpg")
                cv2.imwrite(file_path, image)
                generated_frames.append(file_path)
        self.image_sources += generated_frames
        return generated_frames

    def write_title(self, title: str, color: tuple[int, int, int] | str):
        if isinstance(color, str):
            color = ImageColor.getrgb(color)
        for f in self.canvases:
            img, canvas = self.canvases[f]
            font_size = img.height * 0.18
            font = ImageFont.truetype("fonts/jf-openhuninn-2.1.ttf", font_size)
            canvas.text(
                xy=(img.width / 2, img.height - font_size * 0.4),
                text=title,
                font=font,
                fill=color,
                anchor="mb",
                align="center",
                stroke_width=int(font_size * 0.05),
                stroke_fill=(255, 255, 255),
            )

    def write_subtitle(self, title: str, color: tuple[int, int, int] | str):
        if isinstance(color, str):
            color = ImageColor.getrgb(color)
        for f in self.image_sources:
            img, canvas = self.canvases[f]
            font_size = img.height * 0.08
            font = ImageFont.truetype("fonts/jf-openhuninn-2.1.ttf", font_size)
            canvas.text(
                xy=(img.width * 0.01, img.height * 0.03),
                text=title,
                font=font,
                fill=color,
                anchor="lt",
                align="left",
                stroke_width=int(font_size * 0.08),
                stroke_fill=(255, 255, 255),
            )


if __name__ == "__main__":
    TEST_FILL_COLOR = (101, 166, 181)

    v_obj = ThumbnailGenerator("test.jpg")
    start_time = time()
    # v_obj = ThumbnailGenerator(video_source_path="test.mp4")
    # v_obj.extract_random_frames(10)
    v_obj.load_images_to_canvases()
    v_obj.write_title("もう少しだけ", TEST_FILL_COLOR)
    # v_obj.image_sources = ["test2.jpg"]
    v_obj.write_subtitle("浠Mizuki", TEST_FILL_COLOR)
    v_obj.save_canvases()

    print("Time taken: %f s" % (time() - start_time))
