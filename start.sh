# This script is executed at the start of the relays
# DO NOT MODIFY IT UNLESS YOU REALLY KNOW WHAT YOU ARE DOING!!!

cd $(dirname $0)

while ! (ping -c 1 -W 1 1.2.3.4 | grep -q 'statistics'); do
    echo "Waiting for 1.2.3.4 - network interface might be down..."
    sleep 10
done

sudo -u pi git pull
sh start_relays.sh