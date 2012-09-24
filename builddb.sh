#! /bin/bash

python manage.py syncdb
python manage.py loaddata articleflow/seed.json
