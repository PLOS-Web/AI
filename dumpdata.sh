#! /bin/bash

python manage.py dumpdata --natural articleflow.journal articleflow.state articleflow.transition issues.category > initial_data.json