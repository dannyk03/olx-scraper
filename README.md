## Olx Scraper and Export Project

#### Install python2.7
#### Install project
	git clone <repo>
	pip install -r requirements.txt

#### Set source environment
If you don't install vitualenv:
	
	sudo pip install virtualenv
	virtualenv env
	
	source env/bin/activate

#### Migrate the database:
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