import paho.mqtt.client as mqtt
import asyncio
import time
import json
from paho.mqtt.client import *
from bluepy.btle import Scanner, DefaultDelegate
import sys
import os

from time import ctime


# This class represent the main program of a relay
# It connects to the backend via MQTT and 
class Relay:

    TOPIC_MANAGEMENT = "relay.management"
    TOPIC_UPDATE = "incoming.update"
    MQTT_URL = "mqtt.b-iot.ch"
    MQTT_PORT = 443
    SCAN_TIMEOUT = 2
    WPA_SUPPLICANT_DEFAULT = "ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\nupdate_config=1\ncountry=CH\n\nnetwork={\n\tssid=\\\"Test\\\"\n\tpsk=\\\"12345678\\\"\n}"
    WPA_SUPPLICANT_CONF_PATH = "/etc/wpa_supplicant/wpa_supplicant.conf"



    def __init__(self):
        self.relayID = "relay_raspberry"
        self.company = "biot"
        self.mqttUsername = "testrasp"
        self.mqttPassword = "testrasp"

        self.latitude = 0.0
        self.longitude = 0.0
        self.floor = 0

        self.MAC_ADDRESS_LENGTH_BYTES = 6
        self.certificate_ca_path = "./isrgrootx1.pem"

        self.mqttClient = None
        self.whiteList = []

        self.scanner = Scanner().withDelegate(self.ScanDelegate(self))
        self.beacons = {}

    # Parses the string whiteList passed and return a list of MAC formatted like aa:bb:cc:dd:ee:ff
    def _parse_whiteList(self, whiteListString):
        flag = True
        res = []

        while(flag):
            macAddr = ""
            for i in range(self.MAC_ADDRESS_LENGTH_BYTES):
                index = len(res) + 2*i 
                if index + 1 >= len(whiteListString):
                    flag = False
                    break
                macAddr += whiteListString[index] + whiteListString[index + 1]
                if i < 5:
                    macAddr += ":"
            if not flag:
                break
            res.append(macAddr.lower())
        return res

    def _send_beacons_on_mqtt(self):
        # Example message:
        #{"relayID":"relay_P1","beacons":[{"mac":"fc:02:a0:fa:33:19","rssi":-82,"battery":42,"temperature":24,"status":3}],"latitude":46.51746,"longitude":6.562729,"floor":0} from client relay_P1

        print("Sending beacons to backend...")
        for addr, b in self.beacons.items():
            beaconDoc = b.copy()
            beaconDoc.pop("timeSinceLastMove")
            beaconDoc.pop("txPower")
            beaconDoc.pop("timeSinceLastClick")

            doc = {}
            doc["relayID"] = self.relayID
            doc["beacons"] = [ beaconDoc ]
            doc["latitude"] = self.latitude
            doc["longitude"] = self.longitude
            doc["floor"] = self.floor

            self.mqttClient.publish(self.TOPIC_UPDATE, payload = json.dumps(doc))
        
        self.beacons = {}
        print("Beacons sent to backend!")
    
    def _handle_management_msg(self, msgJson):
        if "reboot" in msgJson and msgJson["reboot"] == True:
            print("reboot command received! rebooting...")
            os.system("sudo reboot")
        
        self._update_parameters_from_backend(msgJson)


    def _update_parameters_from_backend(self, msgJson):
        whiteListString = msgJson["whiteList"]
        print(f"whiteListString = {whiteListString}")

        self.whiteList = self._parse_whiteList(whiteListString)
        print(f"whiteList = {self.whiteList}")

        self.latitude = msgJson["latitude"]
        self.longitude = msgJson["longitude"]

        if "wifi" in msgJson:
            wifi_ssid = msgJson["wifi"]["ssid"]
            wifi_password = msgJson["wifi"]["password"]
            reset = msgJson["wifi"]["reset"]
            self._update_wifi_credentials(wifi_ssid, wifi_password, reset)
    
    def _update_wifi_credentials(self, ssid, password, reset):
        if reset:
            os.system(f"echo \"{self.WPA_SUPPLICANT_DEFAULT}\" | sudo tee {self.WPA_SUPPLICANT_CONF_PATH}")

        # Check that the ssid is not already in the config
        present = False
        wpa_conf = open(self.WPA_SUPPLICANT_CONF_PATH, 'r')
        for l in wpa_conf:
            if "ssid" in l and ssid in l:
                present = True
        if not present:
            to_add = f"\nnetwork={{\n\tssid=\\\"{ssid}\\\"\n\tpsk=\\\"{password}\\\"\n}}"
            os.system(f"echo \"{to_add}\" | sudo tee -a {self.WPA_SUPPLICANT_CONF_PATH}")

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect_mqtt(self, client, userdata, flags, rc):
        print("Connected with result code "+str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe(self.TOPIC_MANAGEMENT, 1)

    def on_disconnect(self, client, userdata, rc):
        client.reconnect()

    # The callback for when a PUBLISH message is received from the server.
    def on_message_mqtt(self, client, userdata, msg):
        print("topic= " + msg.topic+", message = "+str(msg.payload))
        if(msg.topic == self.TOPIC_MANAGEMENT):
            msgJson = json.loads(msg.payload.decode("utf-8"))
            self._handle_management_msg(msgJson)
    
    def connect_mqtt(self):
        # Connect the client to mqtt:
        self.mqttClient = mqtt.Client(client_id=self.relayID, clean_session=True, userdata=None, protocol=MQTTv311, transport="websockets")
        self.mqttClient.will_set("will", payload="{\"company\": \"" + self.company + "\"}", qos=0, retain=False)
        self.mqttClient.username_pw_set(self.mqttUsername, self.mqttPassword)
        # UNCOMMENT TO USE WSS
        #client.tls_set(ca_certs=certificate_ca_path) 
        self.mqttClient.on_connect = self.on_connect_mqtt
        self.mqttClient.on_message = self.on_message_mqtt

        flag_error = True
        while flag_error:
            try:
                self.mqttClient.connect(self.MQTT_URL, port=self.MQTT_PORT, keepalive=60)
                flag_error = False
            except:
                print("Cannot conect, probably due to lack of network. Wait and retry...")
                flag_error = True
                time.sleep(1)
        
        self.mqttClient.loop_start()

    
    async def loop(self):
        while True:
            print("Begin Scan")
            self.scanner.scan(timeout=self.SCAN_TIMEOUT)
            time_sec = int(time.time())
            print(time_sec)
            while time_sec % 3 != 0 :
                time.sleep(0.01)
                time_sec = int(time.time())
            self._send_beacons_on_mqtt()

    
    class ScanDelegate(DefaultDelegate):
        def __init__(self, parent):
            DefaultDelegate.__init__(self)
            self.parent = parent

        def handleDiscovery(self, dev, isNewDev, isNewData):
            if isNewDev:
                macAddr = dev.addr
                if macAddr in self.parent.whiteList:
                    print(macAddr, "RSSI:", dev.rssi, dev.getScanData())
                    beacon = {}
                    beacon["mac"] = macAddr
                    beacon["rssi"] = dev.rssi
                    
                    payload = []
                    # extract from dev.getScanData()
                    beacon["temperature"] = 22 # TODO
                    beacon["battery"] = 42 # TODO
                    beacon["timeSinceLastMove"] = 42 # TODO
                    beacon["txPower"] = 42 # TODO 
                    beacon["timeSinceLastClick"] = 42 # TODO
                    beacon["status"] = 0 # TODO

                    self.parent.beacons[beacon["mac"]] = beacon
            # elif isNewData:
            #     print("Received new data from", dev.addr)


    # Launch BLE loop
    # event_loop = asyncio.get_event_loop()
    # event_loop.run_until_complete(loop())
    # event_loop.close()


async def main():
    relay_instance = Relay()
    relay_instance.connect_mqtt()
    await relay_instance.loop()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
