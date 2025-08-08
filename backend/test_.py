# -*- coding: utf-8 -*-
# @Time : 20-6-9 下午3:06
# @Author : zhuying
# @Company : Minivision
# @File : test_.py
# @Software : PyCharm

import os
import cv2
import numpy as np
import argparse
import warnings
import time

from src.anti_spoof_predict import AntiSpoofPredict
from src.generate_patches import CropImage
from src.utility import parse_model_name
warnings.filterwarnings('ignore')


SAMPLE_IMAGE_PATH = "./sample/"


# 因为安卓端APK获取的视频流宽高比为3:4,为了与之一致，所以将宽高比限制为3:4
def check_image(image):
    height, width, channel = image.shape
    if width/height != 3/4:
        print("Image is not appropriate!!!\nHeight/Width should be 4/3.")
        return False
    else:
        return True


def test(image_path, model_dir, device_id):
    model_test = AntiSpoofPredict(device_id)
    image_cropper = CropImage()

    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Cannot read image from path: {image_path}")

    # не искажай изображение — убери resize или оставь аккуратный
    # image = cv2.resize(image, (image.shape[1], image.shape[0]))

    #result = check_image(image)
    #if result is False:
    #    return 2, 0.0

    image_bbox = model_test.get_bbox(image)
    if image_bbox is None or sum(image_bbox) == 0:
        print("[ERROR] No face detected.")
        return 2, 0.0

    prediction = np.zeros((1, 3))
    for model_name in os.listdir(model_dir):
        h_input, w_input, model_type, scale = parse_model_name(model_name)
        param = {
            "org_img": image,
            "bbox": image_bbox,
            "scale": scale,
            "out_w": w_input,
            "out_h": h_input,
            "crop": True,
        }
        if scale is None:
            param["crop"] = False

        img = image_cropper.crop(**param)
        prediction += model_test.predict(img, os.path.join(model_dir, model_name))

    label = np.argmax(prediction)
    confidence = prediction[0][label] / 2
    print(f"[AntiSpoofing] label = {label}, confidence = {confidence}")
    return label, confidence




if __name__ == "__main__":
    desc = "test"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "--device_id",
        type=int,
        default=0,
        help="which gpu id, [0/1/2/3]")
    parser.add_argument(
        "--model_dir",
        type=str,
        default="./resources/anti_spoof_models",
        help="model_lib used to test")
    parser.add_argument(
        "--image_name",
        type=str,
        default="./sample/image_F1.jpg",
        help="image used to test")
    args = parser.parse_args()
    test(args.image_name, args.model_dir, args.device_id)
