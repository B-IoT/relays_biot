# This script is run by the start.sh script just after having pulled the repository
# Use this to do any job at relay's startup

cd $(dirname $0)

pip3 install -r requirements.txt
rm logs/main_relay.txt 

# TO REMOVE!!! INSTALL HJU CERTIFICATE BEGIN
sudo cp hju.pem /usr/local/share/ca-certificates
sudo update-ca-certificates
# TO REMOVE!!! INSTALL HJU CERTIFICATE END

sudo python3 main_relay.py #>> logs/main_relay.txt 2>&1 &