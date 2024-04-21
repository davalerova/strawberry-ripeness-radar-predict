from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
import shutil
import tempfile
import os
from dotenv import load_dotenv
from roboflow import Roboflow
import boto3

import logging


app = FastAPI()

load_dotenv()

api_key = os.getenv("ROBOFLOW_API_KEY")
bucket_name = os.getenv("S3_BUCKET_NAME")
s3_client = boto3.client('s3', aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                         aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                         region_name=os.getenv("AWS_REGION"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.post("/predict/")
async def create_upload_file(file: UploadFile = File(...)):
    original_filename = file.filename
    logger.info(f"Received file: {original_filename}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(original_filename)[1]) as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_file.flush()  # Asegúrate de vaciar el buffer para que el contenido esté en el disco.
        temp_file_path = temp_file.name

    logger.info(f"Stored temporary file at {temp_file_path}")


    rf = Roboflow(api_key=api_key)
    project = rf.workspace().project("niveles-madurez-fresas")
    model = project.version(1).model

    prediction = model.predict(temp_file_path, confidence=40, overlap=30).json()
    logger.info(f"Prediction: {prediction}")
    # Asegúrate de usar una ruta de archivo válida para la imagen de predicción.
    _, prediction_image_path = tempfile.mkstemp(suffix='.jpg')
    model.predict(temp_file_path, confidence=40, overlap=30).save(prediction_image_path)

    # Sube la imagen de predicción a S3 y asegúrate de manejar el archivo correctamente.
    s3_key = f"predictions/{os.path.basename(prediction_image_path)}"
    with open(prediction_image_path, 'rb') as data:
        s3_client.upload_fileobj(data, bucket_name, s3_key, ExtraArgs={'ACL':'public-read'})

    prediction_image_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
    logger.info(f"Uploaded prediction image to {prediction_image_url}")

    # Limpieza de archivos temporales.
    os.remove(temp_file_path)
    os.remove(prediction_image_path)

    prediction['original_filename'] = original_filename
    prediction['prediction_image_url'] = prediction_image_url
    logger.info(JSONResponse(content=prediction))
    return JSONResponse(content=prediction)
