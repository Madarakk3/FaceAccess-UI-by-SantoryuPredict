import os
import string
import urllib
import uuid
import pickle
import datetime
import time
import shutil

import cv2
from fastapi import FastAPI, File, UploadFile, Form, UploadFile, Response
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import face_recognition
import starlette
from test_ import test
import numpy as np
from src.anti_spoof_predict import AntiSpoofPredict

ATTENDANCE_LOG_DIR = './logs'
DB_PATH = './db'
for dir_ in [ATTENDANCE_LOG_DIR, DB_PATH]:
    if not os.path.exists(dir_):
        os.mkdir(dir_)

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/login")
async def login(file: UploadFile = File(...)):
    # Считываем изображение из байтов
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Приведение к 4:3 — например, 640x480
    img_resized = cv2.resize(img, (640, 480))

    # Сохраняем во временный файл
    temp_filename = f"{uuid.uuid4()}.png"
    cv2.imwrite(temp_filename, img_resized)

    # Передаём путь в антиспуфинг
    label, confidence = test(
        image_path=temp_filename,
        model_dir="./resources/anti_spoof_models",
        device_id=0
    )

    # Если лицо — не подделка
    if label == 1:
        user_name, match_status = recognize(cv2.imread(temp_filename))

        if match_status:
            epoch_time = time.time()
            date = time.strftime('%Y%m%d', time.localtime(epoch_time))
            with open(os.path.join(ATTENDANCE_LOG_DIR, f"{date}.csv"), 'a') as f:
                f.write(f"{user_name},{datetime.datetime.now()},IN\n")
        else:
            user_name = "unknown_person"
            match_status = False
    else:
        user_name = "spoof_detected"
        match_status = False

    # Удалим временное изображение
    os.remove(temp_filename)

    return {
        "user": user_name,
        "match_status": match_status,
        "confidence": float(confidence)
    }

@app.post("/logout")
async def logout(file: UploadFile = File(...)):

    file.filename = f"{uuid.uuid4()}.png"
    contents = await file.read()

    # example of how you can save the file
    with open(file.filename, "wb") as f:
        f.write(contents)

    user_name, match_status = recognize(cv2.imread(file.filename))

    if match_status:
        epoch_time = time.time()
        date = time.strftime('%Y%m%d', time.localtime(epoch_time))
        with open(os.path.join(ATTENDANCE_LOG_DIR, '{}.csv'.format(date)), 'a') as f:
            f.write('{},{},{}\n'.format(user_name, datetime.datetime.now(), 'OUT'))
            f.close()

    return {'user': user_name, 'match_status': match_status}


@app.post("/register_new_user")
async def register_new_user(file: UploadFile = File(...), text: str = None):
    # Уникальное имя файла
    file.filename = f"{uuid.uuid4()}.png"
    contents = await file.read()

    # Сохраняем файл во временную папку
    with open(file.filename, "wb") as f:
        f.write(contents)

    # Дублируем изображение в базу
    shutil.copy(file.filename, os.path.join(DB_PATH, f'{text}.png'))

    # Считываем изображение и переводим его в RGB (важно!)
    img_bgr = cv2.imread(file.filename)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # Получаем эмбеддинги
    embeddings = face_recognition.face_encodings(img_rgb)

    # Если лицо не найдено
    if len(embeddings) == 0:
        os.remove(file.filename)
        return {'registration_status': 400, 'message': 'No face detected'}

    # Сохраняем эмбеддинги в файл
    with open(os.path.join(DB_PATH, f'{text}.pickle'), 'wb') as file_:
        pickle.dump(embeddings, file_)

    print(file.filename, text)

    # Удаляем временный файл
    os.remove(file.filename)

    return {'registration_status': 200}



@app.get("/get_attendance_logs")
async def get_attendance_logs():

    filename = 'out.zip'

    shutil.make_archive(filename[:-4], 'zip', ATTENDANCE_LOG_DIR)

    ##return File(filename, filename=filename, content_type="application/zip", as_attachment=True)
    return starlette.responses.FileResponse(filename, media_type='application/zip',filename=filename)


def recognize(img):
    # it is assumed there will be at most 1 match in the db

    embeddings_unknown = face_recognition.face_encodings(img)
    if len(embeddings_unknown) == 0:
        return 'no_persons_found', False
    else:
        embeddings_unknown = embeddings_unknown[0]

    match = False
    j = 0

    db_dir = sorted([j for j in os.listdir(DB_PATH) if j.endswith('.pickle')])
    # db_dir = sorted(os.listdir(DB_PATH))    
    print(db_dir)
    while ((not match) and (j < len(db_dir))):

        path_ = os.path.join(DB_PATH, db_dir[j])

        file = open(path_, 'rb')
        embeddings = pickle.load(file)[0]

        match = face_recognition.compare_faces([embeddings], embeddings_unknown)[0]

        j += 1

    if match:
        return db_dir[j - 1][:-7], True
    else:
        return 'unknown_person', False

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
