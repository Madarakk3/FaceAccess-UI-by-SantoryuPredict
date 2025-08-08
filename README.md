# FaceAccess System

FaceAccess — это система распознавания лиц с интегрированной защитой от подделки (Anti-Spoofing). Она позволяет:
- Регистрировать пользователей по лицу.
- Выполнять вход/выход в систему с распознаванием лица.
- Детектировать поддельные попытки (например, фото на экране телефона).
- Предотвращать вход при закрытых глазах или других поддельных действиях.

## Визуальные примеры

| № | Описание | Изображение |
|---|----------|-------------|
| 1 | Регистрация пользователя — нажатием на иконку с шестеренкой | ![example1](example1.png) |
| 2 | Вход в систему — нажатием на зелёную кнопку | ![example2](example2.png) |
| 3 | Выход из системы — нажатием на красную кнопку | ![example3](example3.png) |
| 4 | Обнаружение подделки — демонстрация лица с экрана телефона, система говорит "Фейк" | ![example4](example4.png) |
| 5 | Нераспознанный пользователь или лицо с закрытыми глазами — вход запрещён | ![example5](example5.png) |

---

## Backend — установка и запуск

1. Запускаем AWS EC2 инстанс `t2.2xlarge` с Ubuntu.
2. Подключаемся через SSH и выполняем:

```bash
sudo apt update
sudo apt install -y python3-pip nginx software-properties-common python3-virtualenv
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.8 python3.8-dev python3.8-distutils
```

3. Настраиваем Nginx:

```bash
sudo nano /etc/nginx/sites-enabled/fastapi_nginx
```

Вставляем:

```
server {
    listen 80;
    server_name <YOUR_EC2_IP>;
    location / {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

```bash
sudo service nginx restart
```

4. Клонируем проект и запускаем API:

```bash
git clone https://github.com/Madarakk3/FaceAccess-UI-by-SantoryuPredict.git
cd FaceAccess-UI-by-SantoryuPredict/backend
virtualenv venv --python=python3.8
source venv/bin/activate
pip install cmake==3.25.0
pip install -r requirements.txt
python3 -m uvicorn main:app
```

---

## Frontend — установка и запуск

1. Запускаем EC2 инстанс `t2.large`, подключаемся через SSH.
2. Устанавливаем nginx:

```bash
sudo apt update && sudo apt install nginx -y
```

3. Настраиваем `/etc/nginx/sites-enabled/default` аналогично backend, но проксируем на порт 3000.

4. Запускаем фронтенд:

```bash
git clone https://github.com/computervisiondeveloper/face-attendance-web-app-react-python.git
cd face-attendance-web-app-react-python/frontend/face-attendance-web-app-front/
sudo apt install npm
npm install
npm start
```

> Не забудьте изменить `API_BASE_URL` в `src/API.js` на IP backend-сервера.

---

## Лицензия

Проект распространяется под лицензией MIT.