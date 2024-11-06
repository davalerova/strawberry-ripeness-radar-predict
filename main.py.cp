from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles  # Importa StaticFiles
import shutil
import tempfile
import os
from dotenv import load_dotenv
from roboflow import Roboflow

import logging

app = FastAPI()

load_dotenv()

api_key = os.getenv("ROBOFLOW_API_KEY")
local_storage_path = "predictions"  # Directorio local para almacenar las imágenes de predicción

# Crear el directorio si no existe
if not os.path.exists(local_storage_path):
    os.makedirs(local_storage_path)

# Montar el directorio de archivos estáticos
app.mount("/predictions", StaticFiles(directory=local_storage_path), name="predictions")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.post("/predict/")
async def create_upload_file(file: UploadFile = File(...)):
    original_filename = file.filename
    logger.info(f"Received file: {original_filename}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(original_filename)[1]) as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_file.flush()
        temp_file_path = temp_file.name

    logger.info(f"Stored temporary file at {temp_file_path}")

    rf = Roboflow(api_key=api_key)
    project = rf.workspace().project("niveles-madurez-fresas")
    model = project.version(1).model

    prediction = model.predict(temp_file_path, confidence=40, overlap=30).json()
    logger.info(f"Prediction: {prediction}")

    # Generar la ruta completa para guardar la imagen de predicción
    prediction_image_filename = f"prediction_{original_filename}"
    prediction_image_path = os.path.join(local_storage_path, prediction_image_filename)
    model.predict(temp_file_path, confidence=40, overlap=30).save(prediction_image_path)

    # Generar la URL para acceder a la imagen de predicción
    prediction_image_url = f"https://davalnet.com/predictions/{prediction_image_filename}"
    logger.info(f"Saved prediction image at {prediction_image_url}")

    # Limpieza de archivos temporales
    os.remove(temp_file_path)

    prediction['original_filename'] = original_filename
    prediction['prediction_image_url'] = prediction_image_url
    logger.info(JSONResponse(content=prediction))

    return JSONResponse(content=prediction)
