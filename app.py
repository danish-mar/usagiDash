from urllib import request

from flask import Flask, jsonify
import psutil
import time
import subprocess

app = Flask(__name__)

# CPU Usage
@app.route('/api/cpu/usage', methods=['GET'])
def get_cpu_usage():
    return jsonify({'cpu_usage': psutil.cpu_percent(interval=1)})

# CPU Usage by Core
@app.route('/api/cpu/usage_by_core', methods=['GET'])
def get_cpu_usage_by_core():
    return jsonify({'cpu_usage_by_core': psutil.cpu_percent(interval=1, percpu=True)})

@app.route('/api/cpu/temp', methods=['GET'])
def get_cpu_temp():
    try:
        # Fetch temperature data using psutil
        temps = psutil.sensors_temperatures()

        print(temps)

        if not temps:
            return jsonify({'error': 'No temperature sensors found'}), 404

        # Assuming 'coretemp' is the key for CPU temperatures
        if 'coretemp' in temps:
            cpu_temps = temps['coretemp']
            temperatures = []
            for entry in cpu_temps:
                temperatures.append({
                    'label': entry.label or 'CPU',
                    'current': entry.current,   # Current temperature
                    'high': entry.high,         # High threshold (if available)
                    'critical': entry.critical  # Critical threshold (if available)
                })
            return jsonify({'cpu_temperatures': temperatures})
        else:
            return jsonify({'error': 'CPU temperature data not available'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# RAM Usage
@app.route('/api/ram/usage', methods=['GET'])
def get_ram_usage():
    ram = psutil.virtual_memory()
    return jsonify({
        'total_ram': ram.total // (1024 ** 2),  # Convert to MB
        'ram_usage_percent': ram.percent
    })

# System Uptime
@app.route('/api/uptime', methods=['GET'])
def get_uptime():
    uptime_seconds = time.time() - psutil.boot_time()
    uptime_minutes = uptime_seconds // 60
    uptime_hours = uptime_seconds // 3600
    uptime_days = uptime_seconds // (3600 * 24)

    return jsonify({
        'uptime_seconds': int(uptime_seconds),
        'uptime_minutes': int(uptime_minutes),
        'uptime_hours': int(uptime_hours),
        'uptime_days': int(uptime_days)
    })

import subprocess

# Start Service
@app.route('/api/service/start/<service_name>', methods=['POST'])
def start_service(service_name):
    try:
        subprocess.run(['systemctl', 'start', service_name], check=True)
        return jsonify({'status': f'{service_name} started'})
    except subprocess.CalledProcessError:
        return jsonify({'error': f'Failed to start {service_name}'}), 500

# Stop Service
@app.route('/api/service/stop/<service_name>', methods=['POST'])
def stop_service(service_name):
    try:
        subprocess.run(['systemctl', 'stop', service_name], check=True)
        return jsonify({'status': f'{service_name} stopped'})
    except subprocess.CalledProcessError:
        return jsonify({'error': f'Failed to stop {service_name}'}), 500

# Service Status
@app.route('/api/service/status/<service_name>', methods=['GET'])
def service_status(service_name):
    try:
        result = subprocess.run(['systemctl', 'is-active', service_name], stdout=subprocess.PIPE, text=True)
        status = result.stdout.strip()
        return jsonify({'status': status})
    except subprocess.CalledProcessError:
        return jsonify({'error': f'Failed to retrieve status for {service_name}'}), 500


import subprocess

# List all services and their status
@app.route('/api/service/list', methods=['GET'])
def list_services():
    try:
        # Run 'systemctl list-units --type=service --all' command
        result = subprocess.run(
            ['systemctl', 'list-units', '--type=service', '--all', '--no-pager'],
            stdout=subprocess.PIPE,
            text=True
        )

        # Process the output into a readable format
        services = []
        lines = result.stdout.splitlines()[1:]  # Skip the first header line
        for line in lines:
            columns = line.split(None, 4)  # Split line into columns (service name, load, active, status, description)
            if len(columns) >= 5:
                service_info = {
                    'name': columns[0],
                    'load': columns[1],
                    'active': columns[2],
                    'status': columns[3],
                    'description': columns[4]
                }
                services.append(service_info)

        return jsonify({'services': services})

    except subprocess.CalledProcessError as e:
        return jsonify({'error': 'Failed to list services'}), 500


import requests

OPENWEATHER_API_KEY = '535692a0379488604bfc8e03727a9135'

@app.route('/api/weather/<location>', methods=['GET'])
def get_weather(location):
    url = f'http://api.openweathermap.org/data/2.5/weather?q={location}&appid={OPENWEATHER_API_KEY}&units=metric'
    response = requests.get(url).json()

    if response.get('cod') != 200:
        return jsonify({'error': 'Location not found'}), 404

    weather_data = {
        'location': response['name'],
        'temperature': response['main']['temp'],
        'weather': response['weather'][0]['description'],
        'humidity': response['main']['humidity'],
        'wind_speed': response['wind']['speed']
    }
    return jsonify(weather_data)

import dbus

def get_spotify():
    session_bus = dbus.SessionBus()
    spotify_bus = session_bus.get_object("org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2")
    spotify_properties = dbus.Interface(spotify_bus, "org.freedesktop.DBus.Properties")
    return spotify_bus, spotify_properties

# Spotify Play
@app.route('/api/spotify/play', methods=['GET'])
def spotify_play():
    spotify_bus, _ = get_spotify()
    spotify_bus.Play()
    return jsonify({'status': 'playing'})

# Spotify Pause
@app.route('/api/spotify/pause', methods=['GET'])
def spotify_pause():
    spotify_bus, _ = get_spotify()
    spotify_bus.Pause()
    return jsonify({'status': 'paused'})

# Spotify Next
@app.route('/api/spotify/next', methods=['GET'])
def spotify_next():
    spotify_bus, _ = get_spotify()
    spotify_bus.Next()
    return jsonify({'status': 'next track'})

# Spotify Previous
@app.route('/api/spotify/prev', methods=['GET'])
def spotify_prev():
    spotify_bus, _ = get_spotify()
    spotify_bus.Previous()
    return jsonify({'status': 'previous track'})

# Spotify Get Song Name
@app.route('/api/spotify/song/name', methods=['GET'])
def spotify_get_song_name():
    _, spotify_properties = get_spotify()
    metadata = spotify_properties.Get("org.mpris.MediaPlayer2.Player", "Metadata")
    song_name = metadata.get('xesam:title')
    return jsonify({'song_name': song_name})


import os
import subprocess
import json
from flask import Flask, jsonify, request
from functools import wraps  # Import wraps from functools

app = Flask(__name__)

# Load the configuration
with open('config/config.json') as config_file:
    config = json.load(config_file)

# Authentication Decorator
def authenticate(f):
    @wraps(f)  # Use wraps to preserve the original function's metadata
    def wrapper(*args, **kwargs):
        # Get the keyword from the request
        keyword = request.args.get('kword')
        if keyword == config['kword']:
            return f(*args, **kwargs)
        else:
            return jsonify({'error': 'Unauthorized access!'}), 403
    return wrapper

# Route to power off the system
@app.route('/api/power/poweroff', methods=['POST'])
@authenticate
def poweroff():
    try:
        subprocess.run(['shutdown', '-h', 'now'], check=True)
        return jsonify({'status': 'System is powering off.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Route to suspend the system
@app.route('/api/power/suspend', methods=['POST'])
@authenticate
def suspend():
    try:
        subprocess.run(['systemctl', 'suspend'], check=True)
        return jsonify({'status': 'System is suspending.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Route to reboot the system
@app.route('/api/power/reboot', methods=['POST'])
@authenticate
def reboot():
    try:
        subprocess.run(['reboot'], check=True)
        return jsonify({'status': 'System is rebooting.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5009)
