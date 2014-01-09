#! /bin/bash

python manage.py dumpdata --natural articleflow.journal articleflow.state articleflow.transition articleflow.typesetter issues.category auth.group > initial_data.json