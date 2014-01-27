# Article Intelligence 2.0

Switches platform to Django, adds tons of junk.  Hopefully isn't bad.

## Requirements

built for:

1.    django 1.4
2.    python 2.7.3

deb-pendencies:

libmysqlclient-dev python-dev libldap2-dev libsasl2-dev libssl-dev unixodbc-dev libxml2-dev libxslt1-dev

## Instructions

1.	git clone
2.	Create a virtual environment: `cd .. ; virtualenv --no-site-packages env`
3.	Activate the virtual environment `source env/bin/activate`
4.	Install python requriments `cd ai ; pip install -r requirements.pip`
5.	Install rhyno `pip install git+ssh://git@github.com/PLOS-Web/rhyno.git`
5.	Create local settings from template: `cp ai/local_settings_sample.py to ai/local_settings.py`
6.	Look through new ai/local_settings.py and fill in required information
7.	`python manage.py syncdb`
8.	`python manage.py migrate`
9.	`python manage.py runserver --insecure`
10.	(Very optional last step that won't work at all) To start the syncing workers `python ./manage.py celeryd -v 2 -B -s celery -E -l INFO`


## Testing

Run a bunch of (extremely out of date) tests with django's awesome unit testing framework:

`python manage.py test`
