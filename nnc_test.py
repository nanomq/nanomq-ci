from cgi import test
from re import T
import subprocess
import shlex
import os
import paho.mqtt.client as mqtt
from multiprocessing import Process
import time


def test_clean_session():
    clean_session_cmd = shlex.split("mosquitto_sub -t topic -h iot-platform.cloud -p 6301")
    persist_session_cmd = shlex.split("mosquitto_sub -t topic -h iot-platform.cloud -p 6301 -c -i id")
    pub_cmd = shlex.split("mosquitto_pub -m message  -t topic -h iot-platform.cloud -p 6301")

    # persistence session
    process = subprocess.Popen(persist_session_cmd, 
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    try:
        process.wait(2)
    except:
        process.terminate()
        # print('client finished')

    process = subprocess.Popen(pub_cmd, 
                               stdout=subprocess.PIPE,
                               universal_newlines=True)

    process = subprocess.Popen(persist_session_cmd, 
                               stdout=subprocess.PIPE,
                               universal_newlines=True)

    while True:
        output = process.stdout.readline()
        if output.strip() == 'message':
            process.terminate()
            break


    process = subprocess.Popen(clean_session_cmd, 
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    try:
        process.wait(1)
    except:
        process.terminate()


def test_retain():
    retain_pub_cmd = shlex.split("mosquitto_pub -m message  -t topic -h iot-platform.cloud -p 6301 -r")
    clean_retain_pub_cmd = shlex.split("mosquitto_pub -n  -t topic -h iot-platform.cloud -p 6301 -r")
    sub_cmd = shlex.split("mosquitto_sub -t topic -h iot-platform.cloud -p 6301")
    process = subprocess.Popen(retain_pub_cmd, 
                               stdout=subprocess.PIPE,
                               universal_newlines=True)

    process = subprocess.Popen(sub_cmd, 
                               stdout=subprocess.PIPE,
                               universal_newlines=True)

    while True:
        output = process.stdout.readline()
        if output.strip() == 'message':
            process.terminate()
            break

    process = subprocess.Popen(clean_retain_pub_cmd, 
                               stdout=subprocess.PIPE,
                               universal_newlines=True)


def test_v4_v5():
    sub_cmd_v4 = shlex.split("mosquitto_sub -t topic -h iot-platform.cloud -p 6301 -V mqttv311")
    sub_cmd_v5 = shlex.split("mosquitto_sub -t topic -h iot-platform.cloud -p 6301 -V 5")
    pub_cmd_v4 = shlex.split("mosquitto_pub -m message  -t topic -h iot-platform.cloud -p 6301 -V mqttv311")
    pub_cmd_v5 = shlex.split("mosquitto_pub -m message  -t topic -h iot-platform.cloud -p 6301 -V 5")

    process1 = subprocess.Popen(sub_cmd_v4,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)

    time.sleep(1)
    process2 = subprocess.Popen(pub_cmd_v5, 
                               stdout=subprocess.PIPE,
                               universal_newlines=True)

    while True:
        output = process1.stdout.readline()
        if output.strip() == 'message':
            print("pass")
            process1.terminate()
            break

    process3 = subprocess.Popen(sub_cmd_v5, 
                               stdout=subprocess.PIPE,
                               universal_newlines=True)

    time.sleep(1)
    process4 = subprocess.Popen(pub_cmd_v4, 
                               stdout=subprocess.PIPE,
                               universal_newlines=True)

    while True:
        output = process3.stdout.readline()
        if output.strip() == 'message':
            print("pass")
            process3.terminate()
            break
            




if __name__=='__main__':
    test_v4_v5()
    test_clean_session()
    test_retain()



