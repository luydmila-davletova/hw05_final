# Соцсеть Yatube

Социальная сеть блогов. Здесь вы можете опубликовать пост у себя на странице или разместить его в группе, можете подписаться на любимых авторов и прокомментировать пост.

## Инструкции по установке
***- Клонируйте репозиторий:***
```
git clone git@github.com:luydmila-davletova/my_yatube_project.git
```

***- Установите и активируйте виртуальное окружение:***
- для MacOS
```
python3 -m venv venv
```
- для Windows
```
python -m venv venv
source venv/bin/activate
source venv/Scripts/activate
```

***- Установите зависимости из файла requirements.txt:***
```
pip install -r requirements.txt
```

***- Выполните миграции:***
```
python manage.py migrate
```

***- В папке с файлом manage.py выполните команду:***
```
python manage.py runserver
```
