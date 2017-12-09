## Olx Scraper and Export Project

#### Install python2.7
#### Install project
	git clone <repo>	

#### Set source environment
If you don't install vitualenv:
	
	sudo pip install virtualenv
	virtualenv env
	
	source env/bin/activate

	pip install -r requirements.txt

#### Migrate the database:
You should set the db name of your mysql server.
So there is DATABASES variable  in olx-site/settings.py like this.
	
	DATABASES = {
	    'default': {
	        'ENGINE': 'django.db.backends.mysql',
	        'NAME': '<db_name>',
	        'USER': '<username>',
	        'PASSWORD': '<password>',
	        'HOST': '<hostname>',
	    }
	}

You can set the db_name, username, password of your mysql database.
and if mysql host is remote, hostname maybe would be host ip.
but if localhost, you can set hostname with 'localhost'.

	python manage.py makemigrations product
	python manage.py migrate

#### Create a superuser
	python manage.py createsuperuser

#### create Phantomjs for headless browser
node version is 6.9.0
If you are use nvm ( node version manager ):
	
	nvm use 6.9.0
	npm install phantomjs -g


#### Edit crontab entry

	* * * * * python /root/olx-Scraper/cron_task.py