from cgi import test
from curses import termattrs
from operator import is_
from re import S, T
import subprocess
import shlex
import os
import paho.mqtt.client as mqtt
from multiprocessing import Process, Value
import time
import threading
import signal

cnt = 0
non_cnt = 0
shared_cnt = 0
lock = threading.Lock()

def clear_subclients():
    entries = os.popen("pidof mosquitto_sub")

    for line in entries:
        for pid in line.split():
            os.kill(int(pid), signal.SIGKILL)

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

def cnt_substr(cmd, n, message):
    process = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    while True:
        output = process.stdout.readline()
        if message in output:
            n.value += 1

def cnt_message(cmd, n, message):
    process = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    while True:
        output = process.stdout.readline()
        if output.strip() == message:
            n.value += 1

def test_shared_subscription():
    pub_cmd = shlex.split("mosquitto_pub -t topic_share -V 5 -m message -h localhost -p 1883 -d --repeat 10")
    sub_cmd = shlex.split("mosquitto_sub -t '$share/a/topic_share' -h localhost -p 1883")
    sub_cmd_shared = shlex.split("mosquitto_sub -t '$share/b/topic_share' -h localhost -p 1883")
    sub_cmd_non_shared = shlex.split("mosquitto_sub -t topic_share -h localhost -p 1883")
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
    process5 = subprocess.Popen(sub_cmd_shared,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    time.sleep(2)
    process6 = subprocess.Popen(pub_cmd,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)

    t1 = threading.Thread(target=wait_message, args=(process1, 1))
    t2 = threading.Thread(target=wait_message, args=(process2, 1))
    t3 = threading.Thread(target=wait_message, args=(process3, 1))
    t4 = threading.Thread(target=wait_message, args=(process4, 2))
    t5 = threading.Thread(target=wait_message, args=(process5, 3))

    t1.daemon = True
    t2.daemon = True
    t3.daemon = True
    t4.daemon = True
    t5.daemon = True

    t1.start()
    t2.start()
    t3.start()
    t4.start()
    t5.start()
    
    times = 0
    while True:
        lock.acquire()
        if cnt == 10:
            lock.release()
            process1.terminate()
            process2.terminate()
            process3.terminate()
            break
        lock.release()
        times += 1
        time.sleep(1)
        if times == 5:
            print("Shared subscription test failed!")
            return
    
    times = 0
    while True:
        lock.acquire()
        if non_cnt == 10:
            lock.release()
            process4.terminate()
            break
        lock.release()
        times += 1
        time.sleep(1)
        if times == 5:
            print("Shared subscription test failed!")
            return
    
    times = 0
    while True:
        lock.acquire()
        if shared_cnt == 10:
            lock.release()
            process5.terminate()
            break
        lock.release()
        times += 1
        time.sleep(1)
        if times == 5:
            print("Shared subscription test failed!")
            return

    print("Shared subscription test passed!")

def test_topic_alias():
    pub_cmd = shlex.split("mosquitto_pub -t topic -V 5 -m message -D Publish topic-alias 10 -h localhost -p 1883 -d --repeat 10")
    sub_cmd = shlex.split("mosquitto_sub -t topic -h localhost -p 1883")

    cnt = Value('i', 0)
    process1 = Process(target=cnt_message, args=(sub_cmd, cnt, "message"))
    process1.start()
    time.sleep(1)
    process2 = subprocess.Popen(pub_cmd,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)

    times = 0
    while True:
        if cnt.value == 10:
            process1.terminate()
            break
        time.sleep(1)
        times += 1
        if times == 5:
            print("Topic alias test failed!")
            process1.terminate()
            return

    print("Topic alias test passed!")


def test_user_property():
    pub_cmd = shlex.split("mosquitto_pub -h localhost -p 1883 -t topic_test -m aaaa -V 5 -D Publish user-property user property")
    sub_cmd = shlex.split("mosquitto_sub -t 'topic_test' -h localhost -p 1883 -V 5 -F %P")

    cnt = Value('i', 0)
    process1 = Process(target=cnt_message, args=(sub_cmd, cnt, "user:property"))
    process1.start()

    time.sleep(1)
    process2 = subprocess.Popen(pub_cmd,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)

    times = 0
    while True:
        if cnt.value == 1:
            process1.terminate()
            break
        time.sleep(1)
        times += 1
        if times == 5:
            print("User property test failed!")
            process1.terminate()
            return
    print("User property test passed!")

def test_session_expiry():
    pub_cmd = shlex.split("mosquitto_pub -h localhost -p 1883 -t topic_test -m message -V 5 -q 1")
    sub_cmd = shlex.split("mosquitto_sub -t 'topic_test' -h localhost -p 1883  --id client -x 5 -c -q 1 -V 5")

    process1 = subprocess.Popen(sub_cmd,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)

    time.sleep(1)
    process1.terminate()
    process2 = subprocess.Popen(pub_cmd,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    cnt = Value('i', 0)
    process3 = Process(target=cnt_message, args=(sub_cmd, cnt, "message"))
    process3.start()
    time.sleep(4)
    process3.terminate()
    if cnt.value != 1:
        print("failed")
        return

    process2 = subprocess.Popen(pub_cmd,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    process3 = Process(target=cnt_message, args=(sub_cmd, cnt, "message"))
    process3.start()
    process3.terminate()
    time.sleep(2)
    if cnt.value == 1:
        print("Session expiry interval test passed!")
    else:
        print("Session expiry interval test failed")

def test_message_expiry():
    pub_cmd = shlex.split("mosquitto_pub -h localhost -p 1883 -t topic_test -m message -V 5 -q 1 -D publish message-expiry-interval 3 -r")
    sub_cmd = shlex.split("mosquitto_sub -t 'topic_test' -h localhost -p 1883 -q 1 -V 5")

    process1 = subprocess.Popen(pub_cmd,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)

    time.sleep(1)
    cnt = Value('i', 0)
    process2 = Process(target=cnt_message, args=(sub_cmd, cnt, "message"))
    process2.start()
    time.sleep(2)
    process2.terminate()
    if cnt.value != 1:
        print("Message expiry interval test failed!")
        return

    time.sleep(3)
    process2 = Process(target=cnt_message, args=(sub_cmd, cnt, "message"))
    process2.start()
    time.sleep(2)
    process2.terminate()
    if cnt.value == 1:
        print("Message expiry interval test passed!")
    else:
        print("Message expiry interval test failed!")

def test_retain_as_publish():
    pub_retain_cmd = shlex.split("mosquitto_pub -t topic -V 5 -m message -d --retain")
    sub_retain_cmd = shlex.split("mosquitto_sub -t topic -V 5 --retain-as-published -d")
    sub_common_cmd = shlex.split("mosquitto_sub -t topic -V 5 -d")
    pub_clean_retain_cmd = shlex.split("mosquitto_pub -t topic -V 5 -m \"\" -d")

    process1 = subprocess.Popen(pub_retain_cmd,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    cnt = Value('i', 0)
    process2 = Process(target=cnt_substr, args=(sub_common_cmd, cnt, " r0,"))
    process2.start()

    cnt1 = Value('i', 0)
    process3 = Process(target=cnt_substr, args=(sub_retain_cmd, cnt1, " r1,"))
    process3.start()

    time.sleep(1)

    if cnt.value != 1 or cnt1.value != 1:
        print("Retain As Published test failed!")
    else:
        print("Retain As Published test passed!")

    process4 = subprocess.Popen(pub_clean_retain_cmd,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)

    process1.terminate()
    process2.terminate()
    process3.terminate()
    process4.terminate()

    time.sleep(2)
    clear_subclients()

if __name__ == '__main__':
    test_message_expiry()
    test_session_expiry()
    test_user_property()
    test_shared_subscription()
    test_topic_alias()
    test_retain_as_publish()

