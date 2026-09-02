import cv2
import numpy as np
import pytesseract
import json
import argparse
import sys
import requests

def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def extract_fields_with_lmstudio(raw_text):
    url = "http://localhost:1234/v1/chat/completions"
    
    prompt = f"""
You are a precise data extraction assistant. Extract the merchant name, date, and total amount from the raw receipt OCR text below. 

Return ONLY a valid JSON object with exactly these three keys:
- "merchant": string or null
- "date": string or null
- "total": string or null

Try to create any missing data if possible(like 18)04/2007 is 18/04/2007 in date.)
Also provide the date in a standard format (DD-MM-YYYY) if possible. If any of the date's components are missing, return incomplete as date value.
Do not include any markdown formatting (like ```json), explanations, or extra text. Just raw JSON.

Raw OCR Text:
{raw_text}
"""

    payload = {
        "model": "local-model",
        "messages": [
            {"role": "system", "content": "You extract structured receipt data into clean JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0
    }
    
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        res_json = response.json()
        content = res_json["choices"][0]["message"]["content"].strip()
        
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
            
        extracted_data = json.loads(content)
        return extracted_data

    except requests.exceptions.ConnectionError:
        raise ConnectionError("Could not connect to LM Studio. Make sure the local server is running on http://localhost:1234")
    except Exception as e:
        raise RuntimeError(f"Failed to parse fields via LM Studio: {str(e)}")

def process_image(image_path):
    # 1. Load Image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image at: {image_path}")
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 127, 255)

    contours, _ = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
    
    receipt_contour = None
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            receipt_contour = approx
            break

    if receipt_contour is not None:
        pts = receipt_contour.reshape(4, 2)
        rect = order_points(pts)
        (tl, tr, br, bl) = rect
 
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))

        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))

        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]], dtype="float32")

        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(img, M, (maxWidth, maxHeight))
        processed_gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    else:
        processed_gray = gray

    custom_config = r'--oem 3 --psm 6'
    raw_text = pytesseract.image_to_string(processed_gray, config=custom_config)

    receipt_data = extract_fields_with_lmstudio(raw_text)
    
    return json.dumps(receipt_data, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="End-to-End Receipt OCR Pipeline with LM Studio Extraction")
    parser.add_argument("image", type=str, help="Path to the target receipt image file")
    args = parser.parse_args()

    try:
        json_output = process_image(args.image)
        print(json_output)
    except Exception as err:
        error_payload = {"error": str(err)}
        print(json.dumps(error_payload, indent=4))
        sys.exit(1)