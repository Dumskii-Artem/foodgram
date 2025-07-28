## Описание проекта

Проект Foodgram. Yandex-Practicum. Python Backend

**Foodgram** — это онлайн‑платформа для публикации и поиска рецептов.
Пользователи могут:

* регистрироваться и авторизоваться;
* добавлять рецепты с ингредиентами и инструкциями;
* просматривать и фильтровать рецепты по тегам;
* сохранять понравившиеся рецепты в избранное;
* отправить ссылку на рецепт другу
* получить список необходимых покупок для реализации рецепта

## Ссылки на проект

* Сайт: [https://babybear.myddns.me/](https://babybear.myddns.me/)


## Исходный код

GitHub: [Dumskii-Artem](https://github.com/Dumskii-Artem/foodgram.git)


## Технологии.

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)
![DjangoREST](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray)
![JWT](https://img.shields.io/badge/JWT-black?style=for-the-badge&logo=JSON%20web%20tokens)
![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)
![Git](https://img.shields.io/badge/git-%23F05033.svg?style=for-the-badge&logo=git&logoColor=white)

## Архитектура

* **Backend** — Django + DRF (REST API)
* **Frontend** — React (production build)
* **База данных** — PostgreSQL
* **Хранение медиа** — Docker volumes
* **Веб‑сервер** — Gunicorn + Nginx
* **CI/CD** — GitHub Actions, деплой по SSH

## Запуск сервера с докер контейнерами (CI/CD)

В GitHub Actions настроены следующие шаги:

1. Проверка кода линтером flake8
2. Сборка фронтенда (`npm run build`)
3. Сборка и запуск контейнеров Docker
4. Деплой на сервер через SSH с использованием Docker
5. Отправка сообщения в телеграмм

### Для запуска этого процесса нужно руками сделать следующее
- создать репозиторий на GitHub и аккаунт на DockerHub
- заполучить сервер, на котором будет размещен сайт
### добавить на GitHub Repository secrets
Settings->Secrets and variables->Actions
- DOCKER_PASSWORD - пароль на DockerHub
- DOCKER_USERNAME - логин на DockerHub
- HOST_IP - IP адрес вашего сервера, куда хотите поместить сайт
- HOST_SSH_KEY - закрытый ключ (длинный) для подключения к вашему серверу
- HOST_USER - логин на вашем сервере
- SSH_PASSPHRASE - что нужно сказать, заходя на сервер - небольшая строка типа пароля
- TELEGRAM_TO - строка вида 123456789
- TELEGRAM_TOKEN - строка вида 7814787497:*****************-***************gk

### поместить на сервер файлы из папки server
подключение к серверу по протоколу ssh (образец)
```
ssh -i ~/.ssh/yp_16_sprint/yc-d-art-mail.dat yc-user@89.169.164.5
```
файл default следует поместить в папку /etc/nginx/sites-enabled
файл nginx.conf у меня лежит в папке /etc/nginx он у вас есть. в этом файле добавлены 1-2 последних строки.

в папку 
```
cd ~/foodgram/
```    
нужно поместить файлы 
- .env 
у меня он такой
```
POSTGRES_USER=любой_логин
POSTGRES_PASSWORD=любой_пароль
POSTGRES_DB=food
# Добавляем переменные для Django-проекта:
DB_HOST=food_db
DB_PORT=5432
SECRET_KEY=django-insecure-fi#^!#-3qp%ja0dhmf&=s$(v6f%t!*^f*jv2f500jpsr5f4nlk
DEBUG=False
ALLOWED_HOSTS=babybear.myddns.me,89.169.164.5,127.0.0.1,localhost
USE_POSTGRESQL=True
```
и еще 2 файла из папки foodgram/data
- ingredients.json
- tags.json
первый файл можно скопировать командой, второй команда похожая
```
scp -i ~/.ssh/yp_16_sprint/yc-d-art-mail.dat  ./data/ingredients.json yc-user@89.169.164.5:/home/yc-user/foodgram/
```
после этого смело пушим наш расчудесный проект на GitHub

## Локальный запуск Backend + Frontend

### Backend

Клонировать репозиторий:
```
git clone git@github.com:Dumskii-Artem/foodgram.git
```

Перейти в папку с Backend:
```
cd foodgram/backend
```
Cоздать виртуальное окружение для backend:
```
Ubuntu: python3 -m venv env
Windows: py -3.9 -m venv env
```
Активировать виртуальное окружение:
```
Ubuntu: source env/bin/activate
Windows: source ./env/Scripts/activate
    или ./env/Scripts/activate
```
Вот так написать:
```
Ubuntu: python3 -m pip install --upgrade pip
Windows: python -m pip install --upgrade pip
```
Установить зависимости из файла requirements.txt:
```
pip install -r requirements.txt
```
Выполнить миграции:
```
Ubuntu: python3 manage.py migrate
Windows: python manage.py migrate
```
Заполнить данными справочники 
```
python manage.py load_ingredients_json ../data/ingredients.json
python manage.py load_tags_json ../data/tags.json
```

Создать администратора. нужно аккуратно заполнить все поля. они обязательные, почта любая никто проверять не будет
```
Ubuntu: python3 manage.py createsuperuser
Windows: python manage.py createsuperuser
```

Теперь можно запустить сервер Backend
```
Ubuntu: python3 manage.py runserver
Windows: python manage.py runserver
```
и зайти в админку http://127.0.0.1:8000/admin. 

или http://127.0.0.1:8000/api/

Остановить сервер Ctrl+C. 

Теперь можно загрузить коллекцию в Postman и запустить её. Возможно, Вам повезет и все тесты пройдут

### Документация API (доступна при запущенном backend)

* Swagger UI: [http://localhost/api/docs/](http://localhost/api/docs/)
* Redoc: [http://localhost/api/redoc/](http://localhost/api/redoc/)


### Запуск Frontend

Чтобы увидеть работу фронтенда, нужно одновременно запустить фронтенд и бэкенд. Для этого можно испрользовать, например, 2 экземпляра VSCode. Итак, запустили сервер backend и в другом VSCode выполняем

```
 npm install --legacy-peer-deps
```
очень много ругается, но это не должно пугать. в крайнем случае подключите к решению знатоков из ChatGPT

Далее
```
npm start
```
в браузере по умолчанию должна открыться страница http://localhost:3000 нашим проектом. Можно или вновь зарегистрироваться или зайти через админский аккаунт, который Вы уже создали





# наследие высокоразвитых предков

Находясь в папке infra, выполните команду docker-compose up.
При выполнении этой команды контейнер frontend, описанный в docker-compose.yml, 
подготовит файлы, необходимые для работы фронтенд-приложения, 
а затем прекратит свою работу.

По адресу http://localhost изучите фронтенд веб-приложения, 
а по адресу http://localhost/api/docs/ — спецификацию API.

