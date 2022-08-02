#!/usr/local/bin/pytest
import sys
import paho.mqtt.client as mqtt
from paho.mqtt.client import *
from paho.mqtt import *
from paho.mqtt.packettypes import *
from paho.mqtt.properties import *
from multiprocessing import Process, Value
from threading import Thread, Lock

g_send_times = 0
g_recv_times = 0
g_pub_times = 1
g_sub_times = 0

user_properties = [("filename","test.txt"),("count","1")]
topic_alias = 10

def on_message_topic_alias(self, obj, msg):
    print("Receive:" + msg.topic+" "+str(msg.qos)+" "+str(msg.payload))
    assert msg.topic == str(msg.payload, 'utf-8')
    if self._protocol == MQTTv5:
        print("topic alias: " + str(msg.properties.TopicAlias))
        assert msg.properties.TopicAlias == topic_alias
    self.disconnect()

def on_message_user_property(self, obj, msg):
    print("Receive:" + msg.topic+" "+str(msg.qos)+" "+str(msg.payload))
    assert msg.topic == str(msg.payload, 'utf-8')
    if self._protocol == MQTTv5:
        print("user property: " + str(msg.properties.UserProperty))
        assert msg.properties.UserProperty == user_properties
    self.disconnect()

def on_message(self, obj, msg):
    print("Receive:" + msg.topic+" "+str(msg.qos)+" "+str(msg.payload))
    assert msg.topic == str(msg.payload, 'utf-8')
    # if self._protocol == MQTTv5:
    #     assert msg.properties.UserProperty == user_properties
    self.disconnect()

def on_publish(self, obj, mid):
    print("published v" + str(self._protocol))
    self.disconnect()

def on_subscribe(self, obj, mid, granted_qos):
    global g_sub_times
    print("subscribed v4")
    g_sub_times += 1
    
def on_subscribe_v5(self, mqttc, obj, mid, granted_qos):
    global g_sub_times
    print("subscribed v5")
    # print("subscribed" + self.protocol)
    g_sub_times += 1

def func(proto, cmd, topic, prop=None):
    mqttc = mqtt.Client(transport='websockets', protocol=proto)   
    if "user/property" == topic:
        mqttc.on_message = on_message_user_property
    elif "topic/alias" == topic:
        mqttc.on_message = on_message_topic_alias
    else:
        mqttc.on_message = on_message


    mqttc.on_publish = on_publish

    if proto == MQTTv311:
        mqttc.on_subscribe = on_subscribe
    elif proto == MQTTv5:
        mqttc.on_subscribe = on_subscribe_v5

    mqttc.connect("localhost", 8085, 60)

    global g_sub_times
    if proto == MQTTv311:
        if cmd == "sub":
            mqttc.subscribe(topic, 1)
        elif cmd == "pub":
            while g_sub_times == 0:
                continue
            g_sub_times = 0
            mqttc.publish(topic, topic, 1)
    else:
        if cmd == "sub":
            mqttc.subscribe(topic, 1)
            # mqttc.subscribe("v311/to/v5", 1)
        elif cmd == "pub":
            while g_sub_times == 0:
                continue    
            g_sub_times = 0
            mqttc.publish(topic, topic, 1, properties=prop)
    mqttc.loop_forever()

def ws_v4_v5_test():
    # v311 to v5
    t1 = Thread(target=func, args=(MQTTv5, "sub", "v311/to/v5"))
    t1.start()
    t2 = Thread(target=func, args=(MQTTv311, "pub", "v311/to/v5"))
    t2.start()
    time.sleep(0.5)

    # v5 to v311
    t1 = Thread(target=func, args=(MQTTv311, "sub", "v5/to/v311"))
    t1.start()
    t2 = Thread(target=func, args=(MQTTv5, "pub", "v5/to/v311"))
    t2.start()
    time.sleep(0.5)

def ws_user_properties():

    properties=Properties(PacketTypes.PUBLISH)
    properties.UserProperty=user_properties

    t1 = Thread(target=func, args=(MQTTv5, "sub", "user/property"))
    t1.start()
    t2 = Thread(target=func, args=(MQTTv5, "pub", "user/property", properties))
    t2.start()

def ws_topic_alias():
    properties=Properties(PacketTypes.PUBLISH)
    properties.TopicAlias=topic_alias
    t1 = Thread(target=func, args=(MQTTv5, "sub", "topic/alias"))
    t1.start()
    t2 = Thread(target=func, args=(MQTTv5, "pub", "topic/alias", properties))
    t2.start()


ws_v4_v5_test()

ws_user_properties()

ws_topic_alias()