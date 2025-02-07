from flask import Flask, request, jsonify, send_file, render_template, send_from_directory
import logging
import openpyxl
from openpyxl import Workbook
import os
import requests
import threading
import time
import zipfile

import time
import torch
from ultralytics import YOLO 

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)


base_photos_dir = "/home/cyclope/esp32_images"
current_photos_dir = base_photos_dir
os.makedirs(base_photos_dir, exist_ok=True)
esp32_cam_url = "http://192.168.4.17/capture"

model = YOLO("best.pt")   #A changer 

def capture_photo():
    try:
        response = requests.get(esp32_cam_url)
        if response.status_code == 200:
            photo_path = os.path.join(current_photos_dir, f"photo_{int(time.time())}.jpg")
            with open(photo_path, 'wb') as file:
                file.write(response.content)
            logging.info(f"Captured photo saved to: {photo_path}")
        else:
            logging.error(f"Failed to capture photo, status code: {response.status_code}")
    except Exception as e:
        logging.error(f"Error capturing photo: {e}")

def analyze_photo(photo_path):
    try:
        time1 = time.time_ns()
        results = model(photo_path)
        time2 = time.time_ns()
        duration_ms = (time2 - time1) / 1e6
        logging.info(f"Temps d'inférence : {duration_ms:.2f} ms")

        output_dir = "/home/blindgeek/esp32_image_Yolo"
        os.makedirs(output_dir, exist_ok=True)

        for result in results:
            result_path = os.path.join(output_dir, f"result_{int(time.time())}.jpg")
            result.save(filename=result_path)
            logging.info(f"Résultat sauvegardé à {result_path}")
    except Exception as e:
        logging.error(f"Erreur lors de l'analyse de l'image : {e}")
        
def start_photo_capture():
    while True:
        capture_photo()
        time.sleep(1)

photo_capture_thread = threading.Thread(target=start_photo_capture)
photo_capture_thread.daemon = True
photo_capture_thread.start()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/latest_photo')
def latest_photo():
    try:
        photos = sorted(os.listdir(current_photos_dir), reverse=True)
        if len(photos) > 1:
            latest_photo_path = os.path.join(current_photos_dir, photos[1])
            return send_file(latest_photo_path, mimetype='image/jpeg')
        else:
            return jsonify({'message': 'No photos found'}), 404
    except Exception as e:
        logging.error(f"Error fetching latest photo: {e}")
        return str(e), 500

@app.route('/data', methods=['POST'])

@app.route('/photos/<path:filename>')
def download_photo(filename):
    return send_from_directory(current_photos_dir, filename)

@app.route('/download_photos', methods=['GET'])
def download_photos():
    try:
        zip_path = os.path.join(current_photos_dir, "photos.zip")
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for root, dirs, files in os.walk(current_photos_dir):
                for file in files:
                    if file != "photos.zip":
                        zipf.write(os.path.join(root, file),
                                   os.path.relpath(os.path.join(root, file),
                                                   os.path.join(current_photos_dir, '..')))

        logging.info(f"Created zip file: {zip_path}")
        return send_file(zip_path, as_attachment=True)
    except Exception as e:
        logging.error(f"Error creating zip file: {e}")
        return str(e), 500

@app.route('/create_new_photo_folder', methods=['POST'])
def create_new_photo_folder():
    global current_photos_dir
    try:
        new_folder_name = f"photos_{int(time.time())}"
        current_photos_dir = os.path.join(base_photos_dir, new_folder_name)
        os.makedirs(current_photos_dir, exist_ok=True)
        logging.info(f"Created new photo folder: {current_photos_dir}")
        return jsonify({'message': f'New photo folder created: {current_photos_dir}'}), 200
    except Exception as e:
        logging.error(f"Error creating new photo folder: {e}")
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
