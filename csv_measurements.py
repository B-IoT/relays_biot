import paho.mqtt.client as mqtt
import asyncio
import time
import json
from paho.mqtt.client import *
from bluepy.btle import Scanner, DefaultDelegate
import sys

from time import ctime

CSV_FILE_NAME_PREFIX = "measurements"
CSV_FILE_NAME_EXTENSION = ".csv"


class relay:

    TOPIC_PARAMETERS = "update.parameters"
    TOPIC_UPDATE = "incoming.update"
    MQTT_URL = "mqtt.b-iot.ch"
    MQTT_PORT = 443


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
        self.whiteList = [  "f1:96:cd:ee:25:bd",
                            "e2:30:d3:c9:fb:66",
                            "d1:0b:14:b3:18:6a",
                            "d4:80:72:2f:95:aa",
                            "c6:c6:f1:4d:24:13",
                            "e3:6f:28:36:5a:db",
                            "fc:02:a0:fa:33:19",
                            "f5:a8:ef:56:d7:c0",
                            "ef:86:35:dd:c3:f7",
                            "e2:51:e0:31:ee:0e",
                            "f0:15:b5:dd:24:38",
                            "d9:ad:89:d1:a7:75",
                            "d1:cf:96:e7:33:ed",
                            "ff:d8:05:64:9a:9c",
                            "f9:b3:b2:3d:53:a5",
                            "d5:b1:89:8b:b8:c5",
                            "ca:36:8b:4a:a6:1c",
                            "e0:51:30:48:16:e5",
                            "f7:9c:08:9a:42:ed"
                        ]

        self.scanner = Scanner().withDelegate(self.ScanDelegate(self))
        self.beacons = {}

   
    def _write_measures(self):
        f = open(CSV_FILE_NAME, mode='a')
        for addr, b in self.beacons.items():
            beaconDoc = b.copy()
            beaconDoc.pop("timeSinceLastMove")
            beaconDoc.pop("txPower")
            beaconDoc.pop("timeSinceLastClick")

        f.write("address;" + beaconDoc["mac"] + "\nrssi;" + str(beaconDoc["rssi"]) + "\n")

        
        self.beacons = {}
        if f != None:
            f.close()

    
    async def loop(self):
        while True:
            self.scanner.scan(timeout=1)
            self._write_measures()

    
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


async def main():
    relay_instance = relay()
    await relay_instance.loop()


if __name__ == "__main__":
    t = time.localtime()
    CSV_FILE_NAME = CSV_FILE_NAME_PREFIX + "_" + str(t.tm_hour) + "_" + str(t.tm_min) + CSV_FILE_NAME_EXTENSION
    f = open(CSV_FILE_NAME, mode='w')
    f.close()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()

