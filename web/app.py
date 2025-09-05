from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

VISUAL_CROSSING_API_KEY = "YOUR_VISUAL_CROSSING_API_KEY"
TOMORROW_API_KEY = "YOUR_TOMORROW_IO_API_KEY"

def get_coordinates(city):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        results = data.get('results')
        if results:
            lat = results[0]['latitude']
            lon = results[0]['longitude']
            return lat, lon
    return None, None

def get_weather_openmeteo(lat, lon, units):
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&current_weather=true"
        f"&hourly=cape,wind_speed_10m,wind_speed_80m,wind_speed_100m"
        f"&daily=temperature_2m_max,temperature_2m_min,weathercode"
        f"&timezone=auto"
    )
    response = requests.get(url)
    output = ""
    if response.status_code == 200:
        data = response.json()
        cape = data.get('hourly', {}).get('cape', ['N/A'])[0]
        wind_10m = data.get('hourly', {}).get('wind_speed_10m', ['N/A'])[0]
        wind_80m = data.get('hourly', {}).get('wind_speed_80m', ['N/A'])[0]
        wind_100m = data.get('hourly', {}).get('wind_speed_100m', ['N/A'])[0]
        speed_unit = 'mph' if units == 'Imperial' else 'm/s'
        output += f"CAPE: {cape} J/kg\n"
        output += f"Wind Speed 10m: {wind_10m} {speed_unit}\n"
        output += f"Wind Speed 80m: {wind_80m} {speed_unit}\n"
        output += f"Wind Speed 100m: {wind_100m} {speed_unit}\n"
        if wind_10m != 'N/A' and wind_100m != 'N/A':
            try:
                shear = float(wind_100m) - float(wind_10m)
                output += f"Wind Shear (100m-10m): {shear} {speed_unit}\n"
            except ValueError:
                output += "Wind Shear: N/A\n"
        daily = data.get('daily', {})
        dates = daily.get('time', [])
        tempmax = daily.get('temperature_2m_max', [])
        tempmin = daily.get('temperature_2m_min', [])
        output += "\n--- 3-Day Forecast ---\n"
        for i in range(min(3, len(dates))):
            output += f"{dates[i]}: Max: {tempmax[i]}° {'F' if units == 'Imperial' else 'C'}, Min: {tempmin[i]}° {'F' if units == 'Imperial' else 'C'}\n"
    else:
        output += "API error or location not found.\n"
    return output

def get_weather_visualcrossing(city, units, forecast_type='3day'):
    unit_group = 'us' if units == 'Imperial' else 'metric'
    include_param = 'current,days,alerts,hours'
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}?unitGroup={unit_group}&key={VISUAL_CROSSING_API_KEY}&include={include_param}"
    response = requests.get(url)
    output_current = ""
    output_forecast = ""
    output_alerts = ""
    if response.status_code == 200:
        data = response.json()
        current = data.get('currentConditions', {})
        weather = current.get('conditions', 'N/A')
        temp = current.get('temp', 'N/A')
        feels_like = current.get('feelslike', 'N/A')
        humidity = current.get('humidity', 'N/A')
        wind_speed = current.get('windspeed', 'N/A')
        precip = current.get('precip', 'N/A')
        pressure = current.get('pressure', 'N/A')
        uv_index = current.get('uvindex', 'N/A')
        visibility = current.get('visibility', 'N/A')
        sunrise = current.get('sunrise', 'N/A')
        sunset = current.get('sunset', 'N/A')
        temp_unit = '°F' if units == 'Imperial' else '°C'
        speed_unit = 'mph' if units == 'Imperial' else 'km/h'
        precip_unit = 'in' if units == 'Imperial' else 'mm'
        pressure_unit = 'inHg' if units == 'Imperial' else 'hPa'
        vis_unit = 'mi' if units == 'Imperial' else 'km'
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        output_current += f"Current Date & Time: {now}\n"
        output_current += f"Weather in {city}: {weather}\n"
        output_current += f"Temperature: {temp}{temp_unit} (Feels like: {feels_like}{temp_unit})\n"
        output_current += f"Humidity: {humidity}%\n"
        output_current += f"Wind Speed: {wind_speed} {speed_unit}\n"
        output_current += f"Precipitation: {precip} {precip_unit}\n"
        output_current += f"Pressure: {pressure} {pressure_unit}\n"
        output_current += f"UV Index: {uv_index}\n"
        output_current += f"Visibility: {visibility} {vis_unit}\n"
        output_current += f"Sunrise: {sunrise}\n"
        output_current += f"Sunset: {sunset}\n"
        output_forecast += "Forecast:\n"
        days = data.get('days', [])
        output_forecast += "3-Day Forecast:\n"
        for day in days[:3]:
            date = day.get('datetime', 'N/A')
            desc = day.get('description', 'N/A')
            tempmax = day.get('tempmax', 'N/A')
            tempmin = day.get('tempmin', 'N/A')
            output_forecast += f"{date}: {desc}\n  Max: {tempmax}{temp_unit}, Min: {tempmin}{temp_unit}\n"
        alerts = data.get('alerts', [])
        if alerts:
            output_alerts += "Weather Alerts:\n"
            for alert in alerts:
                title = alert.get('event', 'Alert')
                desc = alert.get('description', '')
                starts = alert.get('onset', 'N/A')
                ends = alert.get('ends', 'N/A')
                output_alerts += f"{title}:\n  Starts: {starts}\n  Ends: {ends}\n  {desc}\n"
        else:
            output_alerts += "No active weather alerts.\n"
    else:
        output_current = "City not found or API error.\n"
        output_forecast = ""
        output_alerts = ""
    return output_current, output_forecast, output_alerts

def get_tomorrow_weathercodefullday(lat, lon):
    url = (
        f"https://api.tomorrow.io/v4/timelines?location={lat},{lon}"
        f"&fields=weatherCodeFullDay"
        f"&timesteps=1d"
        f"&units=metric"
        f"&apikey={TOMORROW_API_KEY}"
    )
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            intervals = data.get('data', {}).get('timelines', [{}])[0].get('intervals', [])
            if intervals:
                code = intervals[0]['values'].get('weatherCodeFullDay')
                return code
    except Exception:
        pass
    return None

def get_tomorrow_icon_url(code):
    if code is not None:
        return f"https://raw.githubusercontent.com/Tomorrow-IO-API/tomorrow-weather-codes/master/V2_icons/small/png/{code}_clear_small.png"
    return None

@app.route('/', methods=['GET', 'POST'])
def index():
    weather_data = None
    forecast_data = None
    alerts_data = None
    map_url = None
    tomorrow_icon_url = None
    tomorrow_desc = None
    city = ''
    units = 'Metric'
    if request.method == 'POST':
        city = request.form.get('city')
        units = request.form.get('units', 'Metric')
        lat, lon = get_coordinates(city)
        weather_data, forecast_data, alerts_data = get_weather_visualcrossing(city, units)
        om_data = get_weather_openmeteo(lat, lon, units)
        map_url = f"https://static-maps.yandex.ru/1.x/?ll={lon},{lat}&size=450,450&z=10&l=map&pt={lon},{lat},pm2rdm&lang=en_US"
        code = get_tomorrow_weathercodefullday(lat, lon)
        tomorrow_icon_url = get_tomorrow_icon_url(code)
        tomorrow_desc = str(code)
    return render_template('index.html',
        weather_data=weather_data,
        forecast_data=forecast_data,
        alerts_data=alerts_data,
        om_data=om_data if request.method == 'POST' else None,
        map_url=map_url,
        tomorrow_icon_url=tomorrow_icon_url,
        tomorrow_desc=tomorrow_desc,
        city=city,
        units=units
    )

if __name__ == '__main__':
    app.run(debug=True)
