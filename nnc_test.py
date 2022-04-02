from cgi import test
from re import T
import subprocess
import shlex
import os
import paho.mqtt.client as mqtt
from multiprocessing import Process
import time


def test_clean_session():
    clean_session_cmd = shlex.split("mosquitto_sub -t topic -h localhost -p 1883")
    persist_session_cmd = shlex.split("mosquitto_sub -t topic -h localhost -p 1883 -c -i id")
    pub_cmd = shlex.split("mosquitto_pub -m message  -t topic -h localhost -p 1883")

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
    print("Clean session test passed!")


def test_retain():
    retain_pub_cmd = shlex.split("mosquitto_pub -m message  -t topic -h localhost -p 1883 -r")
    clean_retain_pub_cmd = shlex.split("mosquitto_pub -n  -t topic -h localhost -p 1883 -r")
    sub_cmd = shlex.split("mosquitto_sub -t topic -h localhost -p 1883")
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

    print("Retain test passed!")

def test_v4_v5():
    sub_cmd_v4 = shlex.split("mosquitto_sub -t topic -h localhost -p 1883 -V 311")
    sub_cmd_v5 = shlex.split("mosquitto_sub -t topic -h localhost -p 1883 -V 5")
    pub_cmd_v4 = shlex.split("mosquitto_pub -m message  -t topic -h localhost -p 1883 -V 311")
    pub_cmd_v5 = shlex.split("mosquitto_pub -m message  -t topic -h localhost -p 1883 -V 5")

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
            process3.terminate()
            break
    print("V4/V5 test passed!")
            

def test_will_topic():
    pub_cmd = shlex.split("mosquitto_pub -h localhost -p 1883 -t msg -d -l --will-topic will_topic --will-payload will_payload")
    sub_cmd = shlex.split("mosquitto_sub -t will_topic -h localhost -p 1883")

    process1 = subprocess.Popen(sub_cmd,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)

    time.sleep(1)
    process2 = subprocess.Popen(pub_cmd,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    time.sleep(1)
    process2.terminate()
    process2.kill()
    while True:
        output = process1.stdout.readline()
        if output.strip() == 'will_payload':
            process1.terminate()
            break

    print("Will topic test passed!")



if __name__=='__main__':
    test_will_topic()
    test_v4_v5()
    test_clean_session()
    test_retain()



