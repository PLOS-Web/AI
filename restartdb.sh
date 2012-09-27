#! /bin/bash

mysql -u root --password=gumby -e 'DROP DATABASE ai_dev; CREATE DATABASE ai_dev'
python manage.py syncdb
--python manage.py loaddata articleflow/seed.json
