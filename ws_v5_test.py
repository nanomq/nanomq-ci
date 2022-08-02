#!/usr/local/bin/pytest
import sys
import paho.mqtt.client as mqtt
from paho.mqtt.client import *
from multiprocessing import Process, Value
from threading import Thread, Lock

g_send_times = 0
g_recv_times = 0
g_pub_times = 1
g_sub_times = 0

def on_message(self, obj, msg):
    print("Receive:" + msg.topic+" "+str(msg.qos)+" "+str(msg.payload))
    assert msg.topic == str(msg.payload, 'utf-8')
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

def func(proto, cmd):
    mqttc = mqtt.Client(transport='websockets', protocol=proto)   
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
            mqttc.subscribe("v5/to/v311", 1)
        elif cmd == "pub":
            while g_sub_times == 0:
                continue
            g_sub_times = 0
            mqttc.publish("v311/to/v5", "v311/to/v5", 1)
    else:
        if cmd == "sub":
            mqttc.subscribe("v311/to/v5", 1)
        elif cmd == "pub":
            while g_sub_times == 0:
                continue    
            g_sub_times = 0
            mqttc.publish("v5/to/v311", "v5/to/v311", 1)
    mqttc.loop_forever()

def ws_v4_v5_test():
    # v311 to v5
    t1 = Thread(target=func, args=(MQTTv5, "sub"))
    t1.start()
    t2 = Thread(target=func, args=(MQTTv311, "pub"))
    t2.start()
    time.sleep(0.5)

    # v5 to v311
    t1 = Thread(target=func, args=(MQTTv311, "sub"))
    t1.start()
    t2 = Thread(target=func, args=(MQTTv5, "pub"))
    t2.start()
    time.sleep(0.5)


ws_v4_v5_test()

