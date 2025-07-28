## Описание.

Проект foodgram. Yandex-Practicum. Python Backend

## Технологии.

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)
![DjangoREST](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray)
![JWT](https://img.shields.io/badge/JWT-black?style=for-the-badge&logo=JSON%20web%20tokens)
![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)
![Git](https://img.shields.io/badge/git-%23F05033.svg?style=for-the-badge&logo=git&logoColor=white)

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

