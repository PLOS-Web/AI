# Article Intelligence 2.0

Switches platform to Django, adds tons of junk.  Hopefully isn't bad.

## Requirements

#### built for:

1.    django 1.4
2.    python 2.7.3

#### Package Dependencies:

in ubuntu, for instance:

`sudo apt-get install libmysqlclient-dev python-dev libldap2-dev libsasl2-dev libssl-dev unixodbc-dev libxml2-dev libxslt1-dev`

(warning, this might not be all of them!  If you're getting weird errors from the `pip install -r requirements.pip step` it's probably because you're missing a c dependency.)


## Instructions

### Build it

1.	install dependencies listed above
2.	git clone this repo
3.	Create a virtual environment: `cd .. ; virtualenv --no-site-packages env`
4.	Activate the virtual environment `source env/bin/activate`
5.	Install python requriments `cd ai ; pip install -r requirements.pip`
6.	Install rhyno `pip install git+ssh://git@github.com/PLOS-Web/rhyno.git`
7.	Create local settings from template: `cp ai/local_settings_sample.py to ai/local_settings.py`
8.	Look through new ai/local_settings.py and fill in required information
9.	`python manage.py syncdb`.  Make yourself an admin account.
10.	`python manage.py migrate` (At the end of this, a seed DB fixture should be loaded that should mirror the config on the production server.)
11.	`python manage.py runserver --insecure 0.0.0.0:8000` (0.0.0.0 tells the django servlet that it can respond to remote requests. 8000 tells it to listen on port 8000)
12.	Verify the site is working on your localhost: http://localhost:8000
13.	(Very optional last step that won't work at all unless you got _all_ the config set up) To start the task scheduler `python ./manage.py celeryd -v 2 -B -s celery -E -l INFO`

### Play around with it

Log into the site using the account you made in step 9 above.  Add Articles and other objects to play with.


### Test it

Run a bunch of (extremely out-of-date) tests with django's awesome unit testing framework:

`python manage.py test`
