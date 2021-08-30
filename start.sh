# This script is executed at the start of the relays
# DO NOT MODIFY IT UNLESS YOU REALLY KNOW WHAT YOU ARE DOING!!!

cd $(dirname $0)

sudo -u pi git pull
sh start_relays.sh