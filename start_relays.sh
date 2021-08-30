cd $(dirname $0)

pip3 install -r requirements.txt
sudo python3 main_relay.py &> logs/main_relay.txt