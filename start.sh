# This script is executed at the start of the relays
# It is run with pi as user and started from rc.local
# DO NOT MODIFY IT UNLESS YOU REALLY KNOW WHAT YOU ARE DOING!!!

cd $(dirname $0)

while ! (ping -c 1 -W 1 1.2.3.4 | grep -q 'statistics'); do
    echo "Waiting for 1.2.3.4 - network interface might be down..."
    sleep 10
done

rm -f .git/index.lock
git checkout -- .
git pull

chmod +x start.sh

FILE=/home/pi/biot/config/.config
if test -f "$FILE"; then
    echo "$FILE exists."
    cat $FILE
    chmod +x start_relays.sh
    sh start_relays.sh
else
    sudo raspi-config nonint do_expand_rootfs # Expand the filesystem to fill the SD card
    python3 first_time_config.py
fi
