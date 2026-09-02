from fastapi import FastAPI, UploadFile, File
import tempfile
import os

from pipeline import process_image

app = FastAPI()


@app.post("/ocr")
async def ocr(file: UploadFile = File(...)):

    suffix = os.path.splitext(file.filename)[1]

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
        temp.write(await file.read())
        image_path = temp.name

    try:
        result = process_image(image_path)

        return {
            "success": True,
            "result": result
        }

    finally:
        os.remove(image_path)