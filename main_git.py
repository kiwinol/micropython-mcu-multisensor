import machine
import time
import ubinascii
import webrepl
import dht
import json
import network


from umqtt.simple import MQTTClient

# These defaults are overwritten with the contents of /config.json by load_config()
CONFIG = {
    "broker": "192.168.1.33",
    "user": "*************",
    "password": "*************",
    "sensor_pin_gpio": 2,
    "movement_pin_gpio": 12,
    "client_id": b"esp8266_" + ubinascii.hexlify(machine.unique_id()),
    "topic": b"home",
    "ssid": "ortigi",
}

#Global variables
client = None
sensor_pin = None
movement_pin = None
callbackflag = 0


def setup_pins():
    global sensor_pin
    global movement_pin
    global light_pin
    #temp sensor gipo 15

    sensor_pin = dht.DHT22(machine.Pin(CONFIG['sensor_pin_gpio']))

    light_pin = adc = machine.ADC(0)

    movement_pin = machine.Pin(CONFIG['movement_pin_gpio'], machine.Pin.IN, machine.Pin.PULL_UP)
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

def network_status():
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    networks = (sta.scan())
    ssid = CONFIG['ssid']
    signal_strenght = -100

    for wifi_network in networks:
        if (wifi_network[0].decode("utf-8")) == ssid:
            signal_strenght = wifi_network[3]

    return (ssid,signal_strenght)



def callback(p):
    global callbackflag
    callbackflag = "1"
    #print('pin change', p)

def main():
    global callbackflag

    #work around in case there is a call back before the values have been initialized
    ssid = "unknown"
    signal = "-100"

    while True:
        for count in range(0,60):
            if callbackflag == 0:
                time.sleep(.5)

        #Measure temp humidity
        sensor_pin.measure()
        humidity = int(sensor_pin.humidity())
        temp = int(sensor_pin.temperature())

        #Measure Light
        light_level = int(light_pin.read())

        #Check the network status but only if we are not doing  a callback as
        #it takes a couple of extra seconds to check the network status
        if callbackflag == 0:
            ssid, signal = network_status()

        pythonDictionary = {'Temperature':temp, 'Humidity':humidity, 'Movement':callbackflag, 'Light':light_level, 'SSID':ssid, 'Signal':signal}
        jsonPayload = json.dumps(pythonDictionary)

        client.publish('{}/{}'.format(CONFIG['topic'],
                                          CONFIG['client_id']),
                                          bytes(str(jsonPayload), 'utf-8'))
        print('Temp: {}'.format(temp))
        print('Humidity: {}'.format(humidity))
        print('callbackflag: {}'.format(callbackflag))
        print('light: {}'.format(light_level))
        print('ssid: {}'.format(ssid))
        print('signal: {}'.format(signal))

        callbackflag = 0

if __name__ == '__main__':
    load_config()
    setup_pins()
    client = connect_mqtt()
    main()
