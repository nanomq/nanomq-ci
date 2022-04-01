from cgi import test
from operator import is_
from re import S, T
import subprocess
import shlex
import os
import paho.mqtt.client as mqtt
from multiprocessing import Process
import time
import threading

cnt = 0
non_cnt = 0
shared_cnt = 0
lock = threading.Lock()

def wait_message(process, route):
    global cnt 
    global non_cnt 
    global shared_cnt 
    while True:
        output = process.stdout.readline()
        if output.strip() == 'message':
            lock.acquire()
            if route == 1:
                cnt += 1
            elif route == 2:
                non_cnt += 1
            else:
                shared_cnt += 1
            lock.release()

def test_shared_subscription():
    pub_cmd = shlex.split("mosquitto_pub -t topic_share -V 5 -m message -h iot-platform.cloud -p 6301 -d --repeat 10")
    sub_cmd = shlex.split("mosquitto_sub -t '$share/a/topic_share' -h iot-platform.cloud -p 6301")
    # sub_cmd_shared = shlex.split("mosquitto_sub -t '$share/b/topic_share' -h iot-platform.cloud -p 6301")
    sub_cmd_non_shared = shlex.split("mosquitto_sub -t topic_share -h iot-platform.cloud -p 6301")
    process1 = subprocess.Popen(sub_cmd,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    process2 = subprocess.Popen(sub_cmd,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    process3 = subprocess.Popen(sub_cmd,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    process4 = subprocess.Popen(sub_cmd_non_shared,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    # process5 = subprocess.Popen(sub_cmd_shared,
    #                            stdout=subprocess.PIPE,
    #                            universal_newlines=True)
    time.sleep(2)
    process6 = subprocess.Popen(pub_cmd,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)

    t1 = threading.Thread(target=wait_message, args=(process1, 1))
    t2 = threading.Thread(target=wait_message, args=(process2, 1))
    t3 = threading.Thread(target=wait_message, args=(process3, 1))
    t4 = threading.Thread(target=wait_message, args=(process4, 2))
    # t5 = threading.Thread(target=wait_message, args=(process5, 3))

    t1.daemon = True
    t2.daemon = True
    t3.daemon = True
    t4.daemon = True
    # t5.daemon = True

    t1.start()
    t2.start()
    t3.start()
    t4.start()
    # t5.start()
    
    while True:
        lock.acquire()
        if cnt == 10:
            lock.release()
            process1.terminate()
            process2.terminate()
            process3.terminate()
            break
        lock.release()
        time.sleep(1)
    
    while True:
        lock.acquire()
        if non_cnt == 10:
            lock.release()
            process4.terminate()
            break
        lock.release()
        time.sleep(1)

    # while True:
    #     lock.acquire()
    #     if shared_cnt == 10:
    #         lock.release()
    #         print("pass")
    #         process5.terminate()
    #         break
    #     lock.release()
    #     print(shared_cnt)
    #     time.sleep(1)


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


test_shared_subscription()
test_topic_alias()