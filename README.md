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

### Важный момент чтобы все установилось корректно по этому гайду рекомендую создать ВМ с такими настройками 👇
1. Запускаем AWS EC2 инстанс `t2.2xlarge` или GCP n2-standard-2 (2 vCPUs, 8 GB Memory) с Ubuntu 22.04.5 LTS/Ubuntu 22.04 .
2. Подключаемся через SSH и выполняем:

```bash
sudo apt-get update
sudo apt install -y python3-pip nginx
sudo apt install nano
sudo apt install git
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

cd face-attendance-web-app-react-python

sudo apt update

sudo apt install software-properties-common

sudo add-apt-repository ppa:deadsnakes/ppa

sudo apt install python3.8

sudo apt install python3.8-dev

sudo apt install python3.8-distutils

sudo apt install python3-virtualenv

cd backend

virtualenv venv --python=python3.8

source venv/bin/activate

sudo apt install -y build-essential cmake python3-dev \
    libopenblas-dev liblapack-dev pkg-config

pip install -r requirements.txt

python3 -m uvicorn main:app
```

---

## Frontend — установка и запуск

### Важный момент чтобы все установилось корректно по этому гайду рекомендую создать ВМ с такими настройками 👇
1. Запускаем AWS EC2 инстанс `t2.2xlarge` или GCP n2-standard-2 (2 vCPUs, 8 GB Memory) с Ubuntu 22.04.5 LTS/Ubuntu 22.04 .
2. Подключаемся через SSH.

```bash
sudo apt-get update
sudo apt install -y python3-pip nginx
sudo nano /etc/nginx/sites-enabled/fastapi_nginx
```
4. Устанавливаем nginx:
5. Настраиваем `/etc/nginx/sites-enabled/default` аналогично backend, но проксируем на порт 3000.
```bash
server {
    listen 80;   
    server_name <YOUR_EC2_IP>;    
    location / {        
        proxy_pass http://127.0.0.1:3000;    
    }
}
```
```bash
sudo service nginx restart
```
5. Запускаем фронтенд:

```bash
git clone https://github.com/Madarakk3/FaceAccess-UI-by-SantoryuPredict.git

cd face-attendance-web-app-react-python

cd frontend/face-attendance-web-app-front/

sudo apt-get install npm

npm install

npm start
```

> Не забудьте изменить `API_BASE_URL` в `src/API.js` на IP backend-сервера.

---

## Лицензия

Проект распространяется под лицензией MIT.
