import re
import logging
from celery import shared_task
from django.db import close_old_connections
from django.utils import timezone

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def save_sensor_reading(self, data):
    """
    Celery task to save sensor reading to database asynchronously
    """
    try:
        # Close old connections to avoid connection leaks
        close_old_connections()
        
        # Import model here to avoid circular imports
        from sensors.models import SensorReading
        from sensors.models import IrrigationNode 
        
        # Extract data
        device_id = data.get('device_id')
        timestamp = data.get('timestamp')
        
        # Extract and parse temperature
        temp_raw = data.get('temperature')
        temperature = None
        if temp_raw:
            if isinstance(temp_raw, (int, float)):
                temperature = float(temp_raw)
            elif isinstance(temp_raw, str):
                # Extract first number from string like "26 °B 8D 44"
                numbers = re.findall(r'\d+', temp_raw)
                if numbers:
                    temperature = float(numbers[0])
        
        humidity = data.get('humidity')
        soil_moisture = data.get('soil_moisture')
        raw_data = data.get('raw_data')
        salinity=data.get('salinity')  # Extract salinity if available
        ec=data.get('ec')  # Extract EC if available
        
        # linking sesnosr reading to node via device_id
        node = None
        try:
            node = IrrigationNode.objects.get(device_id=device_id)
        except IrrigationNode.DoesNotExist:
            logger.warning(f'No IrrigationNode found for device_id={device_id}')
        except IrrigationNode.MultipleObjectsReturned:
            node = IrrigationNode.objects.filter(device_id=device_id).first()

        reading = SensorReading.objects.create(
            node=node,           # ← set the FK
            device_id=device_id,
            timestamp=timestamp or timezone.now(),
            temperature=temperature,
            humidity=humidity,
            soil_moisture=soil_moisture,
            raw_data=raw_data,
            salinity=salinity,
            ec=ec,
        )
        
        logger.info(f'✅ Saved sensor reading {reading.id} for device {device_id}: Temp={temperature}, Hum={humidity}, Soil={soil_moisture}')
        return f"Saved reading {reading.id}"
        
    except Exception as exc:
        logger.error(f'❌ Failed to save sensor reading: {exc}')
        # Retry the task
        raise self.retry(exc=exc)