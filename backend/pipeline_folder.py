import cv2
import numpy as np
import pytesseract
import json
import argparse
import sys
import requests
import os

from pipeline import process_image

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


def process_folder(folder_path):
    if not os.path.isdir(folder_path):
        raise ValueError(f"Folder does not exist or is not a directory: {folder_path}")

    image_files = []
    for entry in sorted(os.listdir(folder_path)):
        full_path = os.path.join(folder_path, entry)
        if os.path.isfile(full_path):
            ext = os.path.splitext(entry.lower())[1]
            if ext in SUPPORTED_EXTENSIONS:
                image_files.append(full_path)

    if not image_files:
        raise ValueError(f"No supported receipt images found in folder: {folder_path}")

    results = []
    for image_path in image_files:
        try:
            json_output = process_image(image_path)
            parsed = json.loads(json_output)
            results.append({
                "file": os.path.basename(image_path),
                "data": parsed
            })
        except Exception as exc:
            results.append({
                "file": os.path.basename(image_path),
                "error": str(exc)
            })

    return json.dumps({
        "folder": folder_path,
        "processed_files": len(image_files),
        "results": results
    }, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="End-to-End Receipt OCR Pipeline for a folder of receipt images with LM Studio extraction")
    parser.add_argument("folder", type=str, help="Path to the folder containing receipt image files")
    args = parser.parse_args()

    try:
        json_output = process_folder(args.folder)
        print(json_output)
    except Exception as err:
        error_payload = {"error": str(err)}
        print(json.dumps(error_payload, indent=4))
        sys.exit(1)
