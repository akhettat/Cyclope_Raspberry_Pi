import cv2
import numpy as np
from collections import deque
import time
import os
import subprocess
from ultralytics import YOLO
from multiprocessing import Process, Queue, Manager

# Configuration
stream_url = "http://192.168.4.15/"  # URL du flux ESP32-CAM
fps = 20
buffer_minutes = 60
buffer_size = fps * 60 * buffer_minutes
photo_interval = 3
photo_dir = "/home/cyclope/esp32_images"
output_dir = "/home/cyclope/esp32_image_Yolo"
thresh_Hold = 0.0

os.makedirs(photo_dir, exist_ok=True)
os.makedirs(output_dir, exist_ok=True)

# Chargement du modèle YOLO
model = YOLO("best_medium_augmented.pt")

def capture_frames(frame_queue, photo_queue, save_signal_queue, shared_detection):
    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        print("Erreur : Impossible d'ouvrir le flux vidéo.")
        return
    
    last_photo_time = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Erreur : Impossible de lire le flux vidéo.")
            break

        # Ajout de la date et de l'heure en haut à droite
        current_time_str = time.strftime("%d/%m/%y, %H:%M:%S")
        (text_width, text_height), baseline = cv2.getTextSize(current_time_str,
                                                              cv2.FONT_HERSHEY_SIMPLEX,
                                                              0.7, 2)
        pos_x = frame.shape[1] - text_width - 10  # 10 pixels du bord droit
        pos_y = text_height + 10                   # 10 pixels du haut
        cv2.putText(frame, current_time_str, (pos_x, pos_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Dessiner les rectangles de détection en temps réel (s'ils existent)
        detections = shared_detection.get("detections", [])
        for detection in detections:
            box = detection["box"]
            label = detection["label"]
            conf = detection["conf"]
            cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), (255, 0, 0), 2)
            cv2.putText(frame, f"{label} {conf:.2f}", (box[0], box[1]-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        # Envoi de la frame avec overlay à la file
        frame_queue.put(frame.copy())
        
        # Prendre une photo toutes les X secondes pour le traitement YOLO
        current_time = time.time()
        if current_time - last_photo_time >= photo_interval:
            photo_queue.put(frame.copy())
            last_photo_time = current_time
        
        cv2.imshow("ESP32-CAM Stream", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            save_signal_queue.put(True)
    
    cap.release()
    cv2.destroyAllWindows()

def save_video(frame_queue, save_signal_queue, video_filename):
    frame_buffer = deque(maxlen=buffer_size)
    while True:
        if not frame_queue.empty():
            frame = frame_queue.get()
            frame_buffer.append(frame)
        
        # Vérifier si un signal d'enregistrement est reçu
        if not save_signal_queue.empty():
            save_signal_queue.get()
            print("Enregistrement des X dernières minutes...")
            if len(frame_buffer) == 0:
                print("Aucune image à enregistrer.")
                continue
            
            output_file = os.path.join(output_dir, video_filename)
            height, width, _ = frame_buffer[0].shape
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))
            for f in frame_buffer:
                out.write(f)
            out.release()
            print(f"Vidéo enregistrée sous {output_file}")

def process_yolo(photo_queue, audio_queue, shared_detection):
    while True:
        if not photo_queue.empty():
            frame = photo_queue.get()
            photo_path = os.path.join(photo_dir, f"photo_{int(time.time())}.jpg")
            cv2.imwrite(photo_path, frame)
            print(f"Photo enregistrée : {photo_path}")
            
            try:
                results = model(photo_path)
                detections = []       # Liste des détections pour l'overlay
                detected_classes = set()
                for result in results:
                    # Pour chaque boîte détectée
                    for box in result.boxes:
                        cls_id = int(box.cls)
                        confiance = box.conf.item()
                        if confiance >= thresh_Hold:
                            class_name = model.names[cls_id]
                            detected_classes.add(class_name)
                            # Récupérer les coordonnées sous forme d'entiers
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            detections.append({
                                "box": [x1, y1, x2, y2],
                                "label": class_name,
                                "conf": confiance
                            })
                    # Sauvegarder l'image avec détections (optionnel)
                    result_path = os.path.join(output_dir, f"detected_{int(time.time())}.jpg")
                    result.save(filename=result_path)
                    print(f"Résultat YOLO sauvegardé : {result_path}")
                
                # Mise à jour des détections partagées pour l'affichage en temps réel
                shared_detection["detections"] = detections
                
                # Envoyer pour l'audio les classes détectées (une fois par photo)
                for cls in detected_classes:
                    audio_queue.put(cls)
            except Exception as e:
                print(f"Erreur YOLO : {e}")

def audio_feedback(audio_queue):
    detected_classes = set()
    last_announce = time.time()
    
    while True:
        while not audio_queue.empty():
            detected_classes.add(audio_queue.get())
        
        if time.time() - last_announce >= 10:
            if detected_classes:
                class_list = ", ".join(detected_classes)
                text = f"Détections actuelles : {class_list}"
                subprocess.Popen(['espeak', '-vfr', text])
                detected_classes.clear()
            last_announce = time.time()
        
        time.sleep(0.1)

if __name__ == "__main__":
    # Nommer la première vidéo avec la date/heure de lancement
    program_start_time = time.strftime("%d%m%y_%H%M%S")
    video_filename = f"video_{program_start_time}.avi"
    
    # Création d'un Manager pour partager les détections
    manager = Manager()
    shared_detection = manager.dict()
    shared_detection["detections"] = []
    
    frame_queue = Queue()
    photo_queue = Queue()
    save_signal_queue = Queue()
    audio_queue = Queue()
    
    p1 = Process(target=capture_frames, args=(frame_queue, photo_queue, save_signal_queue, shared_detection))
    p2 = Process(target=save_video, args=(frame_queue, save_signal_queue, video_filename))
    p3 = Process(target=process_yolo, args=(photo_queue, audio_queue, shared_detection))
    p4 = Process(target=audio_feedback, args=(audio_queue,))
    
    p1.start()
    p2.start()
    p3.start()
    p4.start()
    
    p1.join()
    p2.join()
    p3.join()
    p4.join()
