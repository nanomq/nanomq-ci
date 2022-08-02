#!/usr/local/bin/pytest
import sys
import paho.mqtt.client as mqtt
from paho.mqtt.client import *

g_send_times = 0
g_recv_times = 0
g_pub_times = 1

def on_message(self, obj, msg):
    print("Receive:" + msg.topic+" "+str(msg.qos)+" "+str(msg.payload))
    assert msg.topic == str(msg.payload, 'utf-8')
    global g_recv_times 
    g_recv_times += 1

def on_publish(self, obj, mid):
    global g_send_times
    global g_pub_times
    if g_send_times == g_pub_times:
        time.sleep(0.05)
        g_pub_times = 1
        self.disconnect()
    else:
        g_pub_times += 1

class Test(object):
    def init(self, host="localhost", port=8085, tran='websockets', prot=MQTTv5):
        self._host = host
        self._port = port
        self._tran = tran
        self._prot = prot
        self._mqttc = mqtt.Client(transport=self._tran, protocol=prot)   
        self._mqttc.on_message = on_message
        self._mqttc.on_publish = on_publish
    

    def assert_test(self, send_times, sub, pub):
        qos = 2
        global g_send_times
        global g_recv_times
        g_recv_times = 0
        g_send_times = send_times

        # test sub
        while qos >= 0:
            self._mqttc.connect(self._host, self._port, 60)
            self._mqttc.subscribe(sub, qos)
            self._mqttc.publish(pub, pub, 0)
            self._mqttc.publish(pub, pub, 1)
            self._mqttc.publish(pub, pub, 2)
            self._mqttc.loop_forever()
            qos -= 1
        assert g_send_times * 3 == g_recv_times

        g_recv_times = 0
        qos = 2

        # test unsub
        while qos >= 0:
            self._mqttc.connect(self._host, self._port, 60)
            self._mqttc.subscribe(sub, qos)
            self._mqttc.unsubscribe(sub)
            self._mqttc.publish(pub, pub, 0)
            self._mqttc.publish(pub, pub, 1)
            self._mqttc.publish(pub, pub, 2)
            self._mqttc.loop_forever()
            qos -= 1
        assert 0 == g_recv_times


t1 = Test()
t1.init(prot=MQTTv311)
t1.assert_test(3, "test/a/b", "test/a/b")
t1.assert_test(3, "test/+/+", "test/a/b")
t1.assert_test(3, "test/a/+", "test/a/b")
t1.assert_test(3, "test/+/b", "test/a/b")
t1.assert_test(3, "+/+/b", "test/a/b")
t1.assert_test(3, "+/a/+", "test/a/b")
t1.assert_test(3, "+/a/b", "test/a/b")
t1.assert_test(3, "test/#", "test/a/b")

