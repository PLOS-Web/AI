#! /bin/bash

mysql -u root --password=gumby -e 'CREATE DATABASE ai_dev '
python manage.py syncdb