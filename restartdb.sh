#! /bin/bash

mysql -u root --password=thunderclese -e 'DROP DATABASE ai_dev; CREATE DATABASE ai_dev'
python manage.py syncdb

