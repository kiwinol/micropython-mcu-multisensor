import machine
import time
import ubinascii
import webrepl
import dht
import json

from umqtt.simple import MQTTClient

# These defaults are overwritten with the contents of /config.json by load_config()
CONFIG = {
    "broker": "192.168.1.33",
    "user": "********",
    "password": "*********",
    "sensor_pin": 2,
    "client_id": b"esp8266_" + ubinascii.hexlify(machine.unique_id()),
    "topic": b"home",
}

#Global variables
client = None
sensor_pin = None
movement_pin = None
callbackflag = 0


def setup_pins():
    global sensor_pin
    global movement_pin

    sensor_pin = dht.DHT22(machine.Pin(2))

    movement_pin = machine.Pin(12, machine.Pin.IN, machine.Pin.PULL_UP)
    movement_pin.irq(trigger=movement_pin.IRQ_RISING, handler=callback)


def load_config():
    import ujson as json
    try:
        with open("/config.json") as f:
            config = json.loads(f.read())
    except (OSError, ValueError):
        print("Couldn't load /config.json")
        save_config()
    else:
        CONFIG.update(config)
        print("Loaded config from /config.json")

def save_config():
    import ujson as json
    try:
        with open("/config.json", "w") as f:
            f.write(json.dumps(CONFIG))
    except OSError:
        print("Couldn't save /config.json")

def connect_mqtt():
    connected = 0
    time.sleep(5)

    while True:
        client = MQTTClient(CONFIG['client_id'], CONFIG['broker'], 0,CONFIG['user'], CONFIG['password'])
        try:
            client.connect()
            connected = 1
            break
        except:
            print("failed to connect trying again")

    print("Connected to {}".format(CONFIG['broker']))
    return client

def callback(p):
    global callbackflag
    callbackflag = "1"
    print('pin change', p)

def main():
    global callbackflag

    while True:
        for count in range(0,10):
            if callbackflag == 0:
                time.sleep(.5)

        humidity = int(sensor_pin.humidity())
        temp = int(sensor_pin.temperature())
        sensor_pin.measure()

        pythonDictionary = {'Temperature':temp, 'Humidity':humidity, 'Movement':callbackflag}
        jsonPayload = json.dumps(pythonDictionary)

        client.publish('{}/{}'.format(CONFIG['topic'],
                                          CONFIG['client_id']),
                                          bytes(str(jsonPayload), 'utf-8'))
        print('Temp: {}'.format(temp))
        print('Humidity: {}'.format(humidity))
        print('callbackflag: {}'.format(callbackflag))

        callbackflag = 0

if __name__ == '__main__':
    load_config()
    setup_pins()
    client = connect_mqtt()
    main()
