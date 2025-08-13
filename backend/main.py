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

ATTENDANCE_LOG_DIR = './logs'                        # Относительный путь к папке logs В этой директории будут храниться CSV-файлы учёта посещаемости.
DB_PATH = './db'                                     # Относительный путь к папке db.  В этой директории будут храниться изображения и эмбеддинги (.png и .pickle) 
for dir_ in [ATTENDANCE_LOG_DIR, DB_PATH]:           # цикл по двум путям: './logs' и './db'.
    if not os.path.exists(dir_):                     # Ставим условия и проверяем есть ли у нас папки logs db где мы будем хранить фотграфии и логи
        os.mkdir(dir_)                               # Если этих файлов нет, то создаем такие же папки с такими же именами logs и db

app = FastApi()                                      # Создаем наш API

origins = ["*"]                                      # Указываем эти конфигурации чтобы у всех была возможность посетить наш APi

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,                           # Список доменов, которым разрешён доступ
    allow_credentials=True,                          # Разрешаем передачу cookies/авторизационных заголовков
    allow_methods=["*"],                             # Разрешаем любые HTTP-методы (GET, POST, PUT, DELETE )
    allow_headers=["*"],                             # Разрешаем любые заголовки в запросах
)

@app.post("/login")                                     # Первый эндпоинт нашего кода, регистрируем функцию login как обработчик POST-запросов по пути /login.
async def login(file: UploadFile = File(...)):          # Создаем асинхронную функцию login(file: - имя параметра эндпоинта, 
                                                        #                                то есть ключ по которому FastAPI найдёт загруженный файл.
                                                        #                      UploadFile- это способ принять загружаемый файл который не хранит данные файлов в паямти
                                                        #                       File() - вытаскивает файл, то есть идет в тело запроса, Ищет поле с file 
                                                        #                                 и Преобразует это поле в объект UploadFile и передаёт его в функцию) 
                                                        #                       ... внутри File означает что ОБЯЗАТЕЛЬНО принимать файл, если без то вернет None
    # Считываем изображение из байтов
    contents = await file.read()                        # Считываем содержимое файла 
    nparr = np.frombuffer(contents, np.uint8)           # np.frombuffer создаёт массив NumPy( contents считанный файл, 
                                                        #                                    np.uint8 указывает тип элементов — 8-битное беззнаковое целое )
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)         # cv2.imdecode() — функция OpenCV, которая умеет переводить массив байтов в полноценное изображение.
                                                        # cv2.imdecode(nparr наш массив байтов, cv2.IMREAD_COLOR переводим всё дело в цветнное изображение BGR)
    # Приведение к 4:3 — например, 640x480
    img_resized = cv2.resize(img, (640, 480))          # Делаем ресайз изображения потому что модель обучена на изображениях 4:3

    # Сохраняем во временный файл
    temp_filename = f"{uuid.uuid4()}.png"              # Формируем f строку с uuid.uuid4() — функция из модуля uuid, 
                                                       # которая генерирует случайный UUID (универсальный уникальный идентификатор) в .png формате 
    cv2.imwrite(temp_filename, img_resized)            # Записываем файл и соединяем уникальный адрес в png и сам ресайз изображение 
                                                       # то есть этот уникальный адрес содерижит наше изорбажение которое нам нужно будет для антиспуфинга

    # Передаём путь в антиспуфинг
    label, confidence = test(                          # Передаем нашу функцию из test.py test() указываем путь к нашему файлу уникальному, модель спуфинга 
                                                       # и указываем что будем использовать GPU, если нету то CPU можно поставить -1 чтобы только на CPU
        image_path=temp_filename,
        model_dir="./resources/anti_spoof_models",
        device_id=0
    )

    # Если лицо — не подделка
    if label == 1:
        user_name, match_status = recognize(cv2.imread(temp_filename))            # recognise возвращает 2 значение строковый идентификатор (имя) и булевое значение
                                                                                  # найдено ли совпадение или нет. cv2.imread(temp_filename) считываем  наше изображение
        if match_status:
            epoch_time = time.time()                                              # Берем текущее время в секундах
            date = time.strftime('%Y%m%d', time.localtime(epoch_time))            # форматирует локальное время в строку даты вида YYYYMMDD (например, 20250809).
            with open(os.path.join(ATTENDANCE_LOG_DIR, f"{date}.csv"), 'a') as f: # создаем лог в папке logs ./logs/<YYYYMMDD>.csv сохраняем как f
                f.write(f"{user_name},{datetime.datetime.now()},IN\n")            # добавляем строку имя пользователя + время и маркировка вход или выход тут вход(IN)
        else:
            user_name = "unknown_person"                                          # Здесь журнал не пишется, просто подготавливается ответ
                                                                             #если распознавание не прошло то пользователь unknown_person, а совпадение 0, то есть False
            match_status = False
    else:
        user_name = "spoof_detected"                                       # если антиспуфинг распознал подделку (не живое лицо). Не записываем в журнал
        match_status = False

    # Удалим временное изображение
    os.remove(temp_filename)                                               # Удалим временное изображение

    return {
        "user": user_name,                                                 # Возвращаем имя пользователя, совпадения и вероятность антиспуфинга
        "match_status": match_status,
        "confidence": float(confidence)
    }

@app.post("/logout")
async def logout(file: UploadFile = File(...)):

    file.filename = f"{uuid.uuid4()}.png"
    contents = await file.read()

    # example of how you can save the file
    with open(file.filename, "wb") as f:                            # Открываем файл пользователя берем название файла и открываем для записи, если файл существует
                                                                        # обрезать (truncate) до нуля, если не существует — создать и записали как f
        f.write(contents)                                            # Записывает в открытый файл байты из переменной contents

    user_name, match_status = recognize(cv2.imread(file.filename))       # recognise возвращает 2 значение строковый идентификатор (имя) и булевое значение
                                                                    # найдено ли совпадение или нет. cv2.imread(file.filename) считываем  наше изображение

    if match_status:
        epoch_time = time.time()
        date = time.strftime('%Y%m%d', time.localtime(epoch_time))
        with open(os.path.join(ATTENDANCE_LOG_DIR, '{}.csv'.format(date)), 'a') as f:
            f.write('{},{},{}\n'.format(user_name, datetime.datetime.now(), 'OUT'))
            f.close()

    return {'user': user_name, 'match_status': match_status}            # Возвращаем имя пользователя и совпадения


@app.post("/register_new_user")
async def register_new_user(file: UploadFile = File(...), text: str = None):
    # Уникальное имя файла
    file.filename = f"{uuid.uuid4()}.png"
    contents = await file.read()

    # Сохраняем файл во временную папку
    with open(file.filename, "wb") as f:
        f.write(contents)

    # Дублируем изображение в базу
    shutil.copy(file.filename, os.path.join(DB_PATH, f'{text}.png')) # Берёт файл, который вы только что сохранили на диск под именем file.filename 
                                                                                                                                    # (это имя пришло от клиента).
                                                                      # Копирует его в каталог DB_PATH (./db) под именем <text>.png.
                                                                     #  В результате в ./db появляется визуальная копия регистрационного изображения

    # Считываем изображение и переводим его в RGB (важно!)
    img_bgr = cv2.imread(file.filename)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # Получаем эмбеддинги
    embeddings = face_recognition.face_encodings(img_rgb)          # На вход подаётся RGB-изображение; под капотом сначала находятся лица, 
                                                                     #     затем для каждого строится вектор признаков (эмбеддинг).
                                                                # Результат — список эмбеддингов (list[np.ndarray]), по одному на каждое найденное лицо

    # Если лицо не найдено
    if len(embeddings) == 0:                                       # если длина embeddings = 0 удаляем файл и возвращаем сообщение No face detected
        os.remove(file.filename)
        return {'registration_status': 400, 'message': 'No face detected'}

    # Сохраняем эмбеддинги в файл
    with open(os.path.join(DB_PATH, f'{text}.pickle'), 'wb') as file_:      # если всё ок то сохраняем эмбединги и сам файл под названием pickle 
                                                                              # и переводим его в pickle
        pickle.dump(embeddings, file_)

    print(file.filename, text)

    # Удаляем временный файл
    os.remove(file.filename)
 
    return {'registration_status': 200}                                 # признак успешной регистрации



@app.get("/get_attendance_logs")
async def get_attendance_logs():

    filename = 'out.zip'

    shutil.make_archive(filename[:-4], 'zip', ATTENDANCE_LOG_DIR)        # filename[:-4] — отрезает .zip и остаётся out.
                                                                         #shutil.make_archive('out', 'zip', ATTENDANCE_LOG_DIR):
                                                                              #создаёт ZIP-архив с именем out.zip;
                                                                               #в архив помещает весь каталог ATTENDANCE_LOG_DIR ( ./logs);
                                                                                 #структура архива будет соответствовать содержимому ./logs — все CSV за разные даты.

   ## return File(filename, filename=filename, content_type="application/zip", as_attachment=True)
    return starlette.responses.FileResponse(filename, media_type='application/zip',filename=filename) #Используется FileResponse из Starlette для отправки файла клиенту.
                                                                                                     # filename — путь к файлу (out.zip), который нужно отдать.
                                                                                        #media_type='application/zip' — MIME-тип, сообщающий клиенту, что это ZIP-архив.
                                                                            #filename=filename (в параметрах ответа) — имя, под которым браузер предложит сохранить файл.


def recognize(img):
    # it is assumed there will be at most 1 match in the db

    embeddings_unknown = face_recognition.face_encodings(img)         # извлекает эмбеддинги для всех найденных лиц в изображении img (ожидается формат RGB
    if len(embeddings_unknown) == 0:                                  # Если лиц нет (len(...) == 0), сразу возвращает кортеж:
        return 'no_persons_found', False                              # 'no_persons_found' — метка для ответа; False — флаг “нет совпадения”.
    else:                                                              # Если хотя бы одно лицо найдено — берётся только первое ([0]) в списке.
        embeddings_unknown = embeddings_unknown[0]

    match = False                                                      # match — флаг, найдено ли совпадение.
    j = 0                                                                # j — индекс текущего пользователя в списке базы

    db_dir = sorted([j for j in os.listdir(DB_PATH) if j.endswith('.pickle')]) # os.listdir(DB_PATH) — получает список всех файлов в папке ./db.
                                                                              # Фильтруются только .pickle — это файлы с сохранёнными эмбеддингами пользователей.
                                                                             # Список сортируется по имени файла (алфавитно).
                                                                         # Пример: ['ivan_petrov.pickle', 'sergey_ivanov.pickle'].
    print(db_dir)                                                      # print(db_dir) — вывод списка в консоль для отладки.    
  
    while ((not match) and (j < len(db_dir))):            # Цикл перебирает все .pickle в базе, пока не найдено совпадение (not match) и пока не пройдены все файлы.
        path_ = os.path.join(DB_PATH, db_dir[j])          #path_ — полный путь до текущего .pickle.

        file = open(path_, 'rb')                        #Файл открывается в бинарном режиме ('rb').
        embeddings = pickle.load(file)[0]           #  pickle.load(file) загружает список эмбеддингов, сохранённый при регистрации.

        match = face_recognition.compare_faces([embeddings], embeddings_unknown)[0] [0] # берёт первый эмбеддинг пользователя (даже если в файле их несколько).
                                        # face_recognition.compare_faces([embeddings], embeddings_unknown) возвращает список булевых значений, одно на каждое сравнение.
                                        # Здесь сравнивается один эталон с одним неизвестным.
                                       #[0] извлекает булево значение первого (и единственного) сравнения.

        j += 1                    # Если match == True, цикл завершится на следующей проверке условия; если нет, j увеличивается и цикл продолжается.

    if match:                                        #db_dir[j - 1] — имя .pickle файла, в котором нашли совпадение.
                                  #[:-7] отрезает последние 7 символов (точка + слово "pickle") → остаётся чистое имя пользователя, под которым он был зарегистрирован.
                                              #Возвращается (имя_пользователя, True).
                                                #Если совпадения нет — ( 'unknown_person', False ).
        return db_dir[j - 1][:-7], True
    else:
        return 'unknown_person', False
