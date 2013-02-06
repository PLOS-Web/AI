#! /bin/bash

python manage.py dumpdata --natural articleflow.article articleflow.journal articleflow.state articleflow.transition issues.category > initial_data.json