# image pour lancer la pipeline avec OCR sur son poste, sans installer Tesseract
FROM python:3.12.16-slim-trixie
WORKDIR /app

# paquets Debian nécessaires pour l'OCR (tesseract)
RUN apt-get update
RUN apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-fra

# requirements Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# les images
COPY images/ images/

# le code sources
COPY src/ src/
COPY tests/ tests/

# variables d'environnement par défaut (utf-8 et OCR activé)
ENV PYTHONIOENCODING=utf-8
ENV WITH_OCR=1

CMD ["sh", "-c", "python src/generation_data.py && python src/traiter_data.py && pytest -vv"]
