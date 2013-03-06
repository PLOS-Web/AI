# Article Intelligence 2.0

Switches platform to Django, adds tons of junk.  Hopefully isn't bad.

## Requirements

built for:

1.    django 1.4
2.    python 2.7.3

deb-pendencies:

libmysqlclient-dev python-dev libldap2-dev libsasl2-dev libssl-dev

## Instructions

1.	git clone
2.	`cd .. ; virtualenv --no-site-packages env`
3.	`source env/bin/activate`
4.	`cd ai ; pip install -r requirements.txt`
5.	Create local_settings.py (see local_settings_sample.py for a boilerplate)
6.	`python manage.py syncdb`
7.	`python manage.py migrate`
8.	`python manage.py runserver --insecure`


## Testing

Run a bunch of tests with django's awesome unit testing framework:

`python manage.py test`
