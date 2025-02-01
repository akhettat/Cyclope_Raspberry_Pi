import cv2
import numpy as np
from collections import deque
import time
import os

# Configuration
stream_url = "http://192.168.4.16/"  # Remplacez par l'URL du flux ESP32-CAM
fps = 20  # Fréquence d'images par seconde
buffer_minutes = 5  # Nombre de minutes à enregistrer
buffer_size = fps * 60 * buffer_minutes  # Taille de la file circulaire
photo_interval = 1  # Prendre une photo toutes les X secondes
photo_dir = "/home/cyclope/esp32_images"  # Dossier d'enregistrement des photos

# Création du dossier photo si inexistant
os.makedirs(photo_dir, exist_ok=True)

# File circulaire pour stocker les images
frame_buffer = deque(maxlen=buffer_size)
last_photo_time = 0

# Ouvrir le flux vidéo
cap = cv2.VideoCapture(stream_url)
if not cap.isOpened():
    print("Erreur : Impossible d'ouvrir le flux vidéo.")
    exit()

def save_video(frames, fps, output_file="output.avi"):
    if not frames:
        print("Aucune image à enregistrer.")
        return
    
    height, width, _ = frames[0].shape
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

    for frame in frames:
        out.write(frame)

    out.release()
    print(f"Vidéo enregistrée sous {output_file}")

def save_photo(frame):
    global last_photo_time
    current_time = time.time()
    if current_time - last_photo_time >= photo_interval:
        photo_path = os.path.join(photo_dir, f"photo_{int(current_time)}.jpg")
        cv2.imwrite(photo_path, frame)
        print(f"Photo enregistrée : {photo_path}")
        last_photo_time = current_time

print("Démarrage de la capture... Appuyez sur 's' pour enregistrer la vidéo, 'q' pour quitter.")
while True:
    ret, frame = cap.read()
    if not ret:
        print("Erreur : Impossible de lire le flux vidéo.")
        break
    
    frame_buffer.append(frame)
    save_photo(frame)  # Capture et enregistre les photos en temps réel
    
    cv2.imshow("ESP32-CAM Stream", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('s'):
        print("Enregistrement des X dernières minutes...")
        save_video(list(frame_buffer), fps)
        print("Enregistrement terminé.")
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
