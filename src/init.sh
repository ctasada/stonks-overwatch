#!/bin/sh

python src/manage.py npminstall
python src/app.py migrate
python src/app.py runserver
