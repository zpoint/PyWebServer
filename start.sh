homeDir="/home/PyWebServer"
cd $homeDir
nohup python3 -u $homeDir"/main.py" > /dev/null &
echo "Start PyWebServer service..."
