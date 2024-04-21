# Utilizar una imagen oficial de Python como imagen base
FROM python:3.10-slim

# Establecer el directorio de trabajo en el contenedor
WORKDIR /code

# Actualizar el repositorio de paquetes e instalar librerías necesarias
RUN apt-get update \
    && apt-get install -y libgl1-mesa-glx libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de dependencias al directorio actual
COPY requirements.txt .

# Instalar las dependencias
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copiar el resto del código fuente del proyecto al directorio de trabajo
COPY ./app /code/app

# Comando para ejecutar la aplicación usando Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
