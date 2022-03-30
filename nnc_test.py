from cgi import test
from re import T
import subprocess
import shlex

def test_clean_session():
    clean_session_cmd = shlex.split("mosquitto_sub -t topic -h iot-platform.cloud -p 6301")
    persist_session_cmd = shlex.split("mosquitto_sub -t topic -h iot-platform.cloud -p 6301 -c -i id")
    pub_cmd = shlex.split("mosquitto_pub -m message  -t topic -h iot-platform.cloud -p 6301")

    # persistence session
    process = subprocess.Popen(persist_session_cmd, 
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    try:
        process.wait(1)
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



test_clean_session()



