### Python Web Server Based on aiohttp

#### Requirement

	sudo python3 -m pip install -r requirements.txt

#### Run

bind to port 80 require root permission

	vim config.ini # change host and port etc ...
	sudo nohup python3 main.py > /dev/null &

or

	sudo sh start.sh


#### Test

In browser

	http://localhost/

Response:

	Hello Aiohttp!
