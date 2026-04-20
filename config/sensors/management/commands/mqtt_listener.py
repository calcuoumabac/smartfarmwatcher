import paho.mqtt.client as mqtt
import json
import os
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from sensors.tasks import save_sensor_reading  # Import the Celery task

logger = logging.getLogger(__name__)

# TTN Configuration
TTN_HOST = os.environ.get('TTN_HOST', 'eu1.cloud.thethings.network')
TTN_PORT = int(os.environ.get('TTN_PORT', 1883))
TTN_USERNAME = os.environ.get('TTN_USERNAME')
TTN_PASSWORD = os.environ.get('TTN_PASSWORD')
TTN_TOPIC = os.environ.get('TTN_TOPIC', '#')

class Command(BaseCommand):
    help = 'MQTT listener for TTN uplink messages with Celery'

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.stdout.write(self.style.SUCCESS(f'Connected to TTN MQTT broker at {TTN_HOST}'))
            client.subscribe(TTN_TOPIC)
            self.stdout.write(self.style.SUCCESS(f'Subscribed to topic: {TTN_TOPIC}'))
        else:
            self.stderr.write(self.style.ERROR(f'Failed to connect, return code {rc}'))

    def on_message(self, client, userdata, msg):
        """Callback when a message is received - creates Celery task"""
        self.stdout.write(f'Received message on topic: {msg.topic}')
        
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            
            device_id = payload.get('end_device_ids', {}).get('device_id', 'unknown')
            received_at = payload.get('received_at', timezone.now().isoformat())
            
            uplink_message = payload.get('uplink_message', {})
            decoded_payload = uplink_message.get('decoded_payload', {})
            
            # Extract sensor values
            humidity = decoded_payload.get('humidity_pct')
            soil_moisture = decoded_payload.get('soil_moisture')
            temperature_raw = decoded_payload.get('temperature')
            
            # Prepare data for Celery task
            task_data = {
                'device_id': device_id,
                'timestamp': received_at,
                'temperature': temperature_raw,
                'humidity': humidity,
                'soil_moisture': soil_moisture,
                'raw_data': payload
            }
            
            # Send to Celery for async processing
            result = save_sensor_reading.delay(task_data)
            
            self.stdout.write(self.style.SUCCESS(
                f'🚀 Task sent to Celery (ID: {result.id}) for device {device_id}'
            ))
            
        except json.JSONDecodeError as e:
            self.stderr.write(self.style.ERROR(f'JSON decode error: {e}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error processing message: {e}'))

    def handle(self, *args, **options):
        if not TTN_USERNAME or not TTN_PASSWORD:
            self.stderr.write(self.style.ERROR(
                'TTN credentials not set! Please set TTN_USERNAME and TTN_PASSWORD in .env file'
            ))
            return
        
        self.stdout.write('Starting MQTT listener with Celery...')
        self.stdout.write(f'Host: {TTN_HOST}:{TTN_PORT}')
        self.stdout.write(f'Topic: {TTN_TOPIC}')
        
        client = mqtt.Client()
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.username_pw_set(TTN_USERNAME, TTN_PASSWORD)
        
        try:
            client.connect(TTN_HOST, TTN_PORT, keepalive=60)
            client.loop_forever()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nStopping MQTT listener...'))
            client.disconnect()
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Connection error: {e}'))
            raise