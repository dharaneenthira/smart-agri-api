# Smart Agriculture API

Django REST API for India Innovates submission.

## Features
- Farm management (GPS location)
- IoT sensor data ingestion (soil moisture, temperature, pH)
- Weather snapshots (OpenWeatherMap integration ready)
- AI plant disease detection (image upload + prediction)

## Setup
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
