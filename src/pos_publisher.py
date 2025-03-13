import paho.mqtt.client as mqtt
import json
import random
import time

# MQTT Broker Information
BROKER = "10.0.0.223"
PORT = 1883                               # WebSocket Port (Ensure your broker supports this)
TOPIC_1 = "truck1_position"
NODE_NAME = "vehicle_position_publisher"  # Unique name for this node

# Create an MQTT client instance with a custom node name
client = mqtt.Client(client_id=NODE_NAME)

# Define MQTT callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Connected to MQTT broker as '{NODE_NAME}'.")
    else:
        print(f"❌ Connection failed with code {rc}")

client.on_connect = on_connect  # Attach callback function

# Connect to MQTT Broker
try:
    client.connect(BROKER, PORT, 60)
    client.loop_start()
except Exception as e:
    print(f"❌ Connection Error: {e}")
    exit(1)

# Publish position updates
def publish_position():
    while True:
        position = {
            "x": round(random.uniform(0, 20), 2),
            "y": round(random.uniform(0, 10), 2),
            "z": round(random.uniform(0, 20), 2)
        }
        payload = json.dumps(position)
        print(f"[{NODE_NAME}] Publishing:", payload)
        client.publish(TOPIC_1, payload)
        time.sleep(2)  # Publish every 2 seconds

# Run the publisher function
try:
    publish_position()
except KeyboardInterrupt:
    print(f"\n🔌 Stopping MQTT Publisher '{NODE_NAME}'...")
    client.loop_stop()
    client.disconnect()
