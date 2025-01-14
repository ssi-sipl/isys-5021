import paho.mqtt.client as mqtt

MQTT_CHANNEL = "radar_surveillance"

def on_connect(client, userdata, flags, rc):
    print(f"Connected to broker with result code {rc}")
    client.subscribe(MQTT_CHANNEL)

def on_message(client, userdata, msg):
    print(f"Received message: {msg.payload.decode()}")

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect("localhost", 1883, 60)
    client.loop_start()

    try:
        while True:
            pass  # The subscriber will keep running and print received messages
    except KeyboardInterrupt:
        print("Subscriber stopped.")
        client.loop_stop()

if __name__ == "__main__":
    main()
