#!/bin/sh

python src/app.py npminstall
python src/app.py migrate
python src/app.py runserver
