import paho.mqtt.client as mqtt
import json
from paho.mqtt.client import *
import os
import time

class FirstTimeConfig:

    TOPIC_CONFIG = "relay.configuration"
    MQTT_URL = "mqtt.b-iot.ch"
    MQTT_PORT = 443
    DEFAULT_CONF_PATH = "/home/pi/biot/relays_biot/default_config/default.config"
    CONFIG_PATH = "/home/pi/biot/config/.config"
    CERTIFICATE_PATH = "./isrgrootx1.pem"


    def __init__(self):
        flag = True
        try:
            f = open(self.DEFAULT_CONF_PATH, 'r')
        except:
            # Cannot open file
            flag = False
            
        if flag:
            config = json.load(f)
            f.close()

            self.relayID = config["relayID"]
            self.mqttID = config["mqttID"]
            self.mqttUsername = config["mqttUsername"]
            self.mqttPassword = config["mqttPassword"]
        else:
            self.relayID = "relay_0"
            self.mqttID = "relay_0"
            self.mqttUsername = "relayBiot_0"
            self.mqttPassword = "relayBiot_0"


        self.configured = False

        self.mqttClient = None

   

    def send_config_request(self):
        doc = {}
        doc["configuration"] = "ready"
        self.mqttClient.publish(self.TOPIC_CONFIG, payload = json.dumps(doc), qos=1)
    
    def _handle_config_response(self, msgJson):
        # Check that it is not one of our own message that is coming back
        if "relayMessage" not in msgJson and "configuration" not in msgJson:
            if "relayID" not in msgJson or "mqttID" not in msgJson or "mqttUsername" not in msgJson or "mqttPassword" not in msgJson:
                doc = {}
                doc["relayMessage"] = "Error, the given json does not contain one of the following keys: relayID, mqttID, mqttUsername, mqttPassword"
                self.mqttClient.publish(self.TOPIC_CONFIG, payload = json.dumps(doc), qos=1)
            else:
                try:
                    f = open(self.CONFIG_PATH, 'w')
                    json.dump(msgJson, f)
                except:
                    doc = {}
                    doc["relayMessage"] = "An error occured while writing .config file"
                    self.mqttClient.publish(self.TOPIC_CONFIG, payload = json.dumps(doc), qos=1)
                    return
                finally:
                    f.close()

                try:
                    f = open(self.CONFIG_PATH, 'r')
                    written_config = json.load(f)
                except:
                    doc = {}
                    doc["relayMessage"] = "An error occured while reading .config file again"
                    self.mqttClient.publish(self.TOPIC_CONFIG, payload = json.dumps(doc), qos=1)
                    return
                finally:
                    f.close()
                
                doc = {}
                doc["relayMessage"] = "Written config"
                doc["content"] = json.dumps(written_config)
                doc["path"] = self.CONFIG_PATH
                self.mqttClient.publish(self.TOPIC_CONFIG, payload = json.dumps(doc), qos=1)
                self.configured = True

            


    # The callback for when the client receives a CONNACK response from the server.
    def on_connect_mqtt(self, client, userdata, flags, rc):
        print("Connected with result code "+str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe(self.TOPIC_CONFIG, 1)

    def on_disconnect(self, client, userdata, rc):
        client.reconnect()

    # The callback for when a PUBLISH message is received from the server.
    def on_message_mqtt(self, client, userdata, msg):
        print("topic= " + msg.topic+", message = "+str(msg.payload))
        if(msg.topic == self.TOPIC_CONFIG):
            msgJson = json.loads(msg.payload.decode("utf-8"))
            self._handle_config_response(msgJson)
    
    def connect_mqtt(self):
        # Connect the client to mqtt:
        self.mqttClient = mqtt.Client(client_id=self.mqttID, clean_session=True, userdata=None, protocol=MQTTv311, transport="websockets")
        self.mqttClient.will_set("will", payload="{\"company\": \"biot\"}", qos=0, retain=False)
        self.mqttClient.username_pw_set(self.mqttUsername, self.mqttPassword)
        # UNCOMMENT TO USE WSS
        #client.tls_set(ca_certs=self.CERTIFICATE_PATH) 
        self.mqttClient.on_connect = self.on_connect_mqtt
        self.mqttClient.on_message = self.on_message_mqtt

        flag_error = True
        while flag_error:
            try:
                self.mqttClient.connect(self.MQTT_URL, port=self.MQTT_PORT, keepalive=60)
                flag_error = False
            except:
                print("Cannot connect, probably due to lack of network. Wait and retry...")
                flag_error = True
                time.sleep(1)
        
        self.mqttClient.loop_start()




if __name__ == "__main__":
    first_time_instance = FirstTimeConfig()
    first_time_instance.connect_mqtt()
    first_time_instance.send_config_request()
    time.sleep(10)
    while not first_time_instance.configured:
        time.sleep(10)
        print("waiting on configuration...")
        first_time_instance.send_config_request()
    os.system("sudo reboot")
