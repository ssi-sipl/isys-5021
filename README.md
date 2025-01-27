# isys-5021

## Table of Contents

1. [Overview](#overview)
2. [Radar Config](#radar-config)
3. [Important Files](#important-files)
4. [Configuration](#configuration)
5. [Usage](#usage)

## Overview

This repository contains scripts to interface with the radar device, parse its data, and display it using CLI interfaces.

## Radar Config

- **IP Address:** 192.168.252.10
- **Port:** 2050

## Important Files

- **main.py**: The main script to run the radar interface.
- **config.py**: Contains configuration variables for the radar.
- **subscriber.py**: Subscribes to radar data and processes it.

## Configuration

The `config.py` file contains variables that can be adjusted to configure the radar and its data parsing behavior. Below are the key variables:

### MQTT Configuration

- `SEND_MQTT`: Boolean flag to enable or disable sending data via MQTT. Default is `False`.
- `MQTT_BROKER`: The IP address of the MQTT broker. Default is `"localhost"`.
- `MQTT_PORT`: The port number to connect to the MQTT broker. Default is `1883`.
- `MQTT_CHANNEL`: The MQTT channel to publish radar data. Default is `"radar_surveillance"`.
- `MQTT_BROKER_SUBSCRIBER`: The IP address of the MQTT broker for the subscriber. Default is `"localhost"`.

### Radar Configuration

- `RADAR_ID`: The unique identifier for the radar device. Default is `"radar-isys5021"`.
- `AREA_ID`: The identifier for the area being monitored by the radar. Default is `"area-1"`.
- `RADAR_LAT`: The latitude coordinate of the radar's location. Default is `34.011125`.
- `RADAR_LONG`: The longitude coordinate of the radar's location. Default is `74.01219`.
- `LOCAL_IP`: The static IP of the Ethernet. Default is `"192.168.252.2"`.
- `LOCAL_PORT`: The port number for local communication. Default is `2050`.

### Detection Thresholds

- `SNR_THRESHOLD`: The minimum signal-to-noise ratio for valid detection. Default is `3`.
- `SIGNAL_STRENGTH_THRESHOLD`: The minimum valid signal strength in dB. Default is `10`.

### Constants

- `EARTH_R`: The Earth's radius in meters. Default is `6371000`.

### Output Configuration

- `OUTPUT_FILE`: The file where detected targets data will be saved. Default is `"detected_targets.json"`.

### Basic Information

- `MAX_RANGE`: The maximum detection range in meters. Default is `150`.
- `MAX_AZIMUTH`: The maximum azimuth angle in degrees. Default is `75`.

## Usage

1. **Run Main Script**: Execute `main.py` to start the radar interface.

   ```sh
   python main.py
   ```

2. **Configuration**: Adjust settings in `config.py` as needed.

3. **Subscriber**: Use `subscriber.py` to handle radar data subscriptions.
   ```sh
   python subscriber.py
   ```
