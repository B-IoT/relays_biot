# This script is run by the start.sh script just after having pulled the repository
# Use this to do any job at relay's startup

cd $(dirname $0)

pip3 install -r requirements.txt
rm logs/main_relay.txt 

sudo cp hju.pem /usr/local/share/ca-certificates
sudo update-ca-certificates
# # TO REMOVE!!! CHANGE TO HTTPS ORIGIN BEGIN
# git remote set-url origin https://biot-relay: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@github.com/B-IoT/relays_biot.git
# # TO REMOVE!!! CHANGE TO HTTPS ORIGIN END

sudo python3 main_relay.py #>> logs/main_relay.txt 2>&1 &