from cgi import test
import subprocess
import shlex
import os
import paho.mqtt.client as mqtt
from multiprocessing import Process
import time

def test_topic_alias():
    pub_cmd = shlex.split("mosquitto_pub -t topic -V 5 -m message -D Publish topic-alias 10 -h iot-platform.cloud -p 6301 -d --repeat 10")
    sub_cmd = shlex.split("mosquitto_sub -t topic -h iot-platform.cloud -p 6301")

    process1 = subprocess.Popen(sub_cmd,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)

    time.sleep(1)
    process2 = subprocess.Popen(pub_cmd,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
                            

    cnt = 0
    while True:
        output = process1.stdout.readline()
        if output.strip() == 'message':
            cnt += 1
            if cnt == 10:
                process1.terminate()
                print("pass")
                break


test_topic_alias()