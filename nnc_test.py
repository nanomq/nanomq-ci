from cgi import test
from re import T
import subprocess
import shlex
import os
import paho.mqtt.client as mqtt
from multiprocessing import Process, Value
import time

def cnt_message(cmd, n, message):
    process = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    while True:
        output = process.stdout.readline()
        if output.strip() == message:
            n.value += 1

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

    # process = subprocess.Popen(persist_session_cmd, 
    #                            stdout=subprocess.PIPE,
    #                            universal_newlines=True)

    # while True:
    #     output = process.stdout.readline()
    #     if output.strip() == 'message':
    #         process.terminate()
    #         break

    
    cnt = Value('i', 0)
    process = Process(target=cnt_message, args=(persist_session_cmd, cnt, "message"))
    process.start()
    time.sleep(1)
    process.terminate()

    process = subprocess.Popen(clean_session_cmd, 
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    try:
        process.wait(1)
    except:
        process.terminate()

    if cnt.value != 1:
        print("Clean session test failed!")
        return
    
    print("Clean session test passed!")


def test_retain():
    retain_pub_cmd = shlex.split("mosquitto_pub -m message  -t topic -h localhost -p 1883 -r")
    clean_retain_pub_cmd = shlex.split("mosquitto_pub -n  -t topic -h localhost -p 1883 -r")
    sub_cmd = shlex.split("mosquitto_sub -t topic -h localhost -p 1883")
    process = subprocess.Popen(retain_pub_cmd, 
                               stdout=subprocess.PIPE,
                               universal_newlines=True)

    cnt = Value('i', 0)
    process = Process(target=cnt_message, args=(sub_cmd, cnt, "message"))
    process.start()
    time.sleep(1)

    process.terminate()
    process = subprocess.Popen(clean_retain_pub_cmd, 
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    process.terminate()
    if cnt.value != 1:
        print("Retain test failed!")
        return
    print("Retain test passed!")

def test_v4_v5():
    sub_cmd_v4 = shlex.split("mosquitto_sub -t topic -h localhost -p 1883 -V 311")
    sub_cmd_v5 = shlex.split("mosquitto_sub -t topic -h localhost -p 1883 -V 5")
    pub_cmd_v4 = shlex.split("mosquitto_pub -m message  -t topic -h localhost -p 1883 -V 311")
    pub_cmd_v5 = shlex.split("mosquitto_pub -m message  -t topic -h localhost -p 1883 -V 5")

    cnt = Value('i', 0)
    process = Process(target=cnt_message, args=(sub_cmd_v4, cnt, "message"))
    process.start()
    time.sleep(1)
    process2 = subprocess.Popen(pub_cmd_v5, 
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    time.sleep(1)
    process.terminate()

    if cnt.value != 1:
        print("V4/V5 test failed!")
        return

    process = Process(target=cnt_message, args=(sub_cmd_v5, cnt, "message"))
    process.start()
    time.sleep(1)
    process4 = subprocess.Popen(pub_cmd_v4, 
                               stdout=subprocess.PIPE,
                               universal_newlines=True)

    time.sleep(1)
    process.terminate()
    if cnt.value != 2:
        print("V4/V5 test failed!")
        return
    print("V4/V5 test passed!")
            

def test_will_topic():
    pub_cmd = shlex.split("mosquitto_pub -h localhost -p 1883 -t msg -d -l --will-topic will_topic --will-payload will_payload")
    sub_cmd = shlex.split("mosquitto_sub -t will_topic -h localhost -p 1883")

    cnt = Value('i', 0)
    process = Process(target=cnt_message, args=(sub_cmd, cnt, "will_payload"))
    process.start()

    time.sleep(1)
    process2 = subprocess.Popen(pub_cmd,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    time.sleep(1)
    process2.terminate()
    process2.kill()

    times = 0
    while True:
        if cnt.value == 1:
            print("Will topic test passed!")
            break
        time.sleep(1)
        times += 1
        if times == 5:
            print("Will topic test failed!")
            break
    process.terminate()


if __name__=='__main__':
    test_will_topic()
    test_v4_v5()
    test_clean_session()
    test_retain()



