# This script is executed at the start of the relays
# It is run with pi as user and started from rc.local
# DO NOT MODIFY IT UNLESS YOU REALLY KNOW WHAT YOU ARE DOING!!!

cd $(dirname $0)

while ! (ping -c 1 -W 1 1.2.3.4 | grep -q 'statistics'); do
    echo "Waiting for 1.2.3.4 - network interface might be down..."
    sleep 10
done

git checkout -- .
git pull
chmod +x start_relays.sh
sh start_relays.sh