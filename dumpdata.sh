#! /bin/bash

python manage.py dumpdata --natural articleflow.journal articleflow.state articleflow.transition issues.category auth.user auth.group > initial_data.json