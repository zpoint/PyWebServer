### Python Web Server Based on aiohttp

#### Requirement

	sudo python3 -m pip install -r requirements.txt

#### Run

bind to port 80 require root permission
If you don't want to run as root, change port in **main.py**

	sudo nohup python3 main.py > /dev/null &

or (need to change path in start.sh first)

	sudo sh start.sh


#### Test

In browser

	http://localhost/

Response:

	Hello Aiohttp!