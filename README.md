# 🌤️ skies

A beautiful terminal weather app with no API key required.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- 🌡️ **Current conditions** — temperature, feels like, humidity, wind, UV index
- ⏱️ **24-hour hourly forecast** — temperature, rain probability, conditions
- 📅 **7-day forecast** — highs/lows, rain chance, wind speed
- 📍 **Auto location detection** — detects your city via IP, no setup needed
- 🌍 **Any city** — search by name, works globally
- 🌡️ **Celsius & Fahrenheit** — your choice
- 🎨 **Beautiful rendering** — color-coded temperatures, weather icons, clean layout

## Install

```bash
git clone https://github.com/30Sana/TerminalWeatherApp.git
cd skies
pip install -r requirements.txt
```

## Usage

```bash
# Auto-detect your location
python weather.py

# Specific city
python weather.py London
python weather.py "New York"
python weather.py Tokyo

# Fahrenheit
python weather.py --units fahrenheit
python weather.py Miami --units fahrenheit

# Skip sections
python weather.py --no-hourly
python weather.py --no-daily
```

## Data Sources

- **Weather**: [Open-Meteo](https://open-meteo.com/) — free, no API key, no rate limits
- **Geocoding**: [Open-Meteo Geocoding API](https://open-meteo.com/en/docs/geocoding-api)
- **IP Location**: [ip-api.com](https://ip-api.com/) — free tier, no key needed

## Requirements

- Python 3.8+
- `rich`
- `requests`

## License

MIT
