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

* [Сайт](https://babybear.myddns.me/)
* [Админка](https://babybear.myddns.me/admin/)
* [Дока к API сервера](https://babybear.myddns.me/api/)


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

### поместить на сервер файлы из папки server
подключение к серверу по протоколу ssh (образец)
```
ssh -i ~/.ssh/yp_16_sprint/yc-d-art-mail.dat yc-user@89.169.164.5
```
файл default следует поместить в папку /etc/nginx/sites-enabled,

файл nginx.conf у меня лежит в папке /etc/nginx он у вас есть. в этом файле добавлены 1-2 последних строки.

### в папку
```
cd ~/foodgram/
```    
нужно поместить файлы 
- .env (пример для копирования)
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
RECIPE_SHORT_LINK = 'babybear.myddns.me/recipes/'
```


```
### на удаленном сервере заходим в контейнер
```
sudo docker exec -it foodgram-backend-1 bash
```
делаем миграции
```
python manage.py migrate
```
создаем администратора
```
python manage.py createsuperuser
```
запускаем скрипты для заполнения базы
```
python manage.py load_ingredients_json ingredients.json
python manage.py load_tags_json tags.json
```
### переходим по ссылке
* [Адрес сервера](https://babybear.myddns.me/)

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
Выполнить:
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
Ubuntu:
python3 manage.py load_ingredients_json ../data/ingredients.json
python3 manage.py load_tags_json ../data/tags.json
Windows:
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
и [Админка]( http://127.0.0.1:8000/admin)

и [Документация к API сервера](http://127.0.0.1:8000/api/docs)

Остановить сервер Ctrl+C. 

### Документация API (доступна при запущенном backend)

* Swagger UI: [http://localhost/api/docs/](http://localhost/api/docs/)
* Redoc: [http://localhost/api/redoc/](http://localhost/api/redoc/)


### Запуск Frontend

Находясь в папке infra, выполните команду docker-compose up.
При выполнении этой команды контейнер frontend, описанный в docker-compose.yml, 
подготовит файлы, необходимые для работы фронтенд-приложения, 
а затем прекратит свою работу.

По адресу [http://localhost]http://localhost изучите фронтенд веб-приложения, 

а по адресу [http://localhost/api/docs/]http://localhost/api/docs/ — спецификацию API.

