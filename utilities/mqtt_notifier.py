# utilities/mqtt_notifier.py
import paho.mqtt.client as mqtt

def send_excel_generated_message(
    msg="Excel generated",
    topic="excel/status",
    host="app.ilens.io",
    port=1883
):
    try:
        client = mqtt.Client()
        client.connect(host, port, 60)
        client.publish(topic, msg)
        client.disconnect()
    except Exception as e:
        print(f"MQTT publish failed: {e}")
