#! /bin/bash

mysql -u root --password=gumby -e 'DROP DATABASE ai_dev'
./startdb.sh

