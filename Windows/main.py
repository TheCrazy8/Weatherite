import requests
import os
import json
import hashlib
import math
import tkinter as tk
from tkinter import messagebox, scrolledtext
from tkinter import ttk
import sv_ttk
from datetime import datetime
from PIL import Image, ImageTk
import io
import threading
import webbrowser
# For date picker and charting
try:
    from tkcalendar import DateEntry
except ImportError:
    DateEntry = None
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
except ImportError:
    plt = None

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
    print("Could not find coordinates for city.")
    return None, None

def get_weather_openmeteo(lat, lon, units):
    unit_group = 'imperial' if units == 'Imperial' else 'metric'
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
        # Forecasts for next 3 days
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

def get_weather_visualcrossing(city, api_key, units, forecast_type='3day'):
    unit_group = 'us' if units == 'Imperial' else 'metric'
    include_param = 'current,days,alerts,hours'
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}?unitGroup={unit_group}&key={api_key}&include={include_param}"
    response = requests.get(url)
    output_current = ""
    output_forecast = ""
    output_alerts = ""
    if response.status_code == 200:
        data = response.json()
        # Current
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
        # Forecast
        output_forecast += "Forecast:\n"
        if forecast_type == '3day':
            days = data.get('days', [])
            output_forecast += "3-Day Forecast:\n"
            for day in days[:3]:
                date = day.get('datetime', 'N/A')
                desc = day.get('description', 'N/A')
                tempmax = day.get('tempmax', 'N/A')
                tempmin = day.get('tempmin', 'N/A')
                output_forecast += f"{date}: {desc}\n  Max: {tempmax}{temp_unit}, Min: {tempmin}{temp_unit}\n"
        elif forecast_type == '5day':
            days = data.get('days', [])
            output_forecast += "5-Day Forecast:\n"
            for day in days[:5]:
                date = day.get('datetime', 'N/A')
                desc = day.get('description', 'N/A')
                tempmax = day.get('tempmax', 'N/A')
                tempmin = day.get('tempmin', 'N/A')
                output_forecast += f"{date}: {desc}\n  Max: {tempmax}{temp_unit}, Min: {tempmin}{temp_unit}\n"
        elif forecast_type == 'week':
            days = data.get('days', [])
            output_forecast += "7-Day Forecast:\n"
            for day in days[:7]:
                date = day.get('datetime', 'N/A')
                desc = day.get('description', 'N/A')
                tempmax = day.get('tempmax', 'N/A')
                tempmin = day.get('tempmin', 'N/A')
                output_forecast += f"{date}: {desc}\n  Max: {tempmax}{temp_unit}, Min: {tempmin}{temp_unit}\n"
        elif forecast_type in ['1hour', '12hour', '24hour']:
            hours = data.get('hours', [])
            if forecast_type == '1hour':
                output_forecast += "Next Hour Forecast:\n"
                for hour in hours[:1]:
                    time = hour.get('datetime', 'N/A')
                    temp = hour.get('temp', 'N/A')
                    desc = hour.get('conditions', 'N/A')
                    feelslike = hour.get('feelslike', 'N/A')
                    humidity = hour.get('humidity', 'N/A')
                    wind = hour.get('windspeed', 'N/A')
                    output_forecast += f"{time}: {desc}, Temp: {temp}{temp_unit}, Feels like: {feelslike}{temp_unit}, Humidity: {humidity}%, Wind: {wind} {speed_unit}\n"
            elif forecast_type == '12hour':
                output_forecast += "Next 12 Hours Forecast:\n"
                for hour in hours[:12]:
                    time = hour.get('datetime', 'N/A')
                    temp = hour.get('temp', 'N/A')
                    desc = hour.get('conditions', 'N/A')
                    feelslike = hour.get('feelslike', 'N/A')
                    humidity = hour.get('humidity', 'N/A')
                    wind = hour.get('windspeed', 'N/A')
                    output_forecast += f"{time}: {desc}, Temp: {temp}{temp_unit}, Feels like: {feelslike}{temp_unit}, Humidity: {humidity}%, Wind: {wind} {speed_unit}\n"
            elif forecast_type == '24hour':
                output_forecast += "Next 24 Hours Forecast:\n"
                for hour in hours[:24]:
                    time = hour.get('datetime', 'N/A')
                    temp = hour.get('temp', 'N/A')
                    desc = hour.get('conditions', 'N/A')
                    feelslike = hour.get('feelslike', 'N/A')
                    humidity = hour.get('humidity', 'N/A')
                    wind = hour.get('windspeed', 'N/A')
                    output_forecast += f"{time}: {desc}, Temp: {temp}{temp_unit}, Feels like: {feelslike}{temp_unit}, Humidity: {humidity}%, Wind: {wind} {speed_unit}\n"
        # Alerts
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

# Historical weather function
# Fetch historical weather for a date range, return list of daily dicts
def get_historical_weather_range_visualcrossing(city, api_key, units, start_date, end_date):
    unit_group = 'us' if units == 'Imperial' else 'metric'
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}/{start_date}/{end_date}?unitGroup={unit_group}&key={api_key}&include=days"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get('days', [])
    return []

# Format stats and summary for a range
def format_historical_stats(days, units, city, start_date, end_date):
    if not days:
        return f"No historical data found for {city} from {start_date} to {end_date}.\n"
    tempmaxs = [d.get('tempmax') for d in days if d.get('tempmax') is not None]
    tempmins = [d.get('tempmin') for d in days if d.get('tempmin') is not None]
    precips = [d.get('precip') for d in days if d.get('precip') is not None]
    humidities = [d.get('humidity') for d in days if d.get('humidity') is not None]
    temp_unit = '°F' if units == 'Imperial' else '°C'
    summary = f"Historical Weather for {city} from {start_date} to {end_date}:\n"
    summary += f"Days: {len(days)}\n"
    if tempmaxs:
        summary += f"Avg Max Temp: {sum(tempmaxs)/len(tempmaxs):.1f}{temp_unit}\n"
        summary += f"Max Temp: {max(tempmaxs):.1f}{temp_unit}\n"
        summary += f"Min Temp: {min(tempmaxs):.1f}{temp_unit}\n"
    if tempmins:
        summary += f"Avg Min Temp: {sum(tempmins)/len(tempmins):.1f}{temp_unit}\n"
    if precips:
        summary += f"Total Precipitation: {sum(precips):.2f}\n"
        summary += f"Avg Precipitation: {sum(precips)/len(precips):.2f}\n"
    if humidities:
        summary += f"Avg Humidity: {sum(humidities)/len(humidities):.1f}%\n"
    return summary

def get_google_static_map(lat, lon):
    # Yandex Static Maps API (no API key required)
    # See: https://yandex.com/dev/maps/staticapi/doc/1.x/dg/concepts/map_params.html
    url = (
        f"https://static-maps.yandex.ru/1.x/?ll={lon},{lat}&size=450,450&z=10&l=map&pt={lon},{lat},pm2rdm&lang=en_US"
    )
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.content
    except Exception:
        pass
    return None

# OpenWeatherMap layers supported: clouds_new, precipitation_new, pressure_new, wind_new, temp_new
OPENWEATHERMAP_LAYERS = [
    ("None", None),
    ("Clouds", "clouds_new"),
    ("Precipitation", "precipitation_new"),
    ("Pressure", "pressure_new"),
    ("Wind", "wind_new"),
    ("Temperature", "temp_new"),
]

def get_tomorrow_weathercodefullday(lat, lon, api_key):
    # Tomorrow.io Timeline API: https://docs.tomorrow.io/reference/timelines
    # We'll get weatherCodeFullDay for today
    url = (
        f"https://api.tomorrow.io/v4/timelines?location={lat},{lon}"
        f"&fields=weatherCodeFullDay"
        f"&timesteps=1d"
        f"&units=metric"
        f"&apikey={api_key}"
    )
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            intervals = data.get('data', {}).get('timelines', [{}])[0].get('intervals', [])
            if intervals:
                code = intervals[0]['values'].get('weatherCodeFullDay')
                return code
    except Exception as e:
        print(f"Tomorrow.io weatherCodeFullDay error: {e}")
    return None

# Mapping of Tomorrow.io weather codes to descriptions and icons
TOMORROW_WEATHER_CODES = {
    1000: ("Clear", "☀️"),
    1100: ("Mostly Clear", "🌤️"),
    1101: ("Partly Cloudy", "⛅"),
    1102: ("Mostly Cloudy", "🌥️"),
    1001: ("Cloudy", "☁️"),
    2000: ("Fog", "🌫️"),
    2100: ("Light Fog", "🌫️"),
    4000: ("Drizzle", "🌦️"),
    4001: ("Rain", "🌧️"),
    4200: ("Light Rain", "🌦️"),
    4201: ("Heavy Rain", "🌧️"),
    5000: ("Snow", "❄️"),
    5001: ("Flurries", "🌨️"),
    5100: ("Light Snow", "🌨️"),
    5101: ("Heavy Snow", "❄️"),
    6000: ("Freezing Drizzle", "🌧️"),
    6001: ("Freezing Rain", "🌧️"),
    6200: ("Light Freezing Rain", "🌧️"),
    6201: ("Heavy Freezing Rain", "🌧️"),
    7000: ("Ice Pellets", "🧊"),
    7101: ("Heavy Ice Pellets", "🧊"),
    7102: ("Light Ice Pellets", "🧊"),
    8000: ("Thunderstorm", "⛈️"),
}

def get_tomorrow_icon_url(code):
    # Use Tomorrow.io icons from GitHub repo
    # Example: https://raw.githubusercontent.com/Tomorrow-IO-API/tomorrow-weather-codes/master/V2_icons/small/png/{code}_clear_small.png
    if code is not None:
        return f"https://raw.githubusercontent.com/Tomorrow-IO-API/tomorrow-weather-codes/master/V2_icons/small/png/{code}_clear_small.png"
    return None

def show_weather():
    city = city_entry.get()
    units = units_var.get()
    # Map forecast dropdown text to value
    forecast_type = next((value for text, value in [
        ('3-Day', '3day'),
        ('5-Day', '5day'),
        ('1 Hour', '1hour'),
        ('12 Hour', '12hour'),
        ('24 Hour', '24hour'),
        ('Week', 'week'),
    ] if text == forecast_var.get()), '3day')
    if not city:
        messagebox.showerror("Error", "Please enter a city name.")
        return
    api_key = "GD85JQAPJ8T44X8VKURGLFFD9"  # Visual Crossing API key
    tomorrow_api_key = "ku1mDhkjQlc8CRZkOzXr8wZ0BjTEUInB"  # Tomorrow.io API key from UI
    vc_current, vc_forecast, vc_alerts = get_weather_visualcrossing(city, api_key, units, forecast_type)
    lat = getattr(city_entry, 'lat', None)
    lon = getattr(city_entry, 'lon', None)
    if lat is None or lon is None:
        lat, lon = get_coordinates(city)
    om_current = ""
    tomorrow_icon_img = None
    tomorrow_desc = ""
    if lat is not None and lon is not None:
        om_data = get_weather_openmeteo(lat, lon, units)
        if "--- 3-Day Forecast ---" in om_data:
            om_parts = om_data.split("--- 3-Day Forecast ---")
            om_current = om_parts[0]
        else:
            om_current = om_data
        # Get Tomorrow.io weatherCodeFullDay
        code = get_tomorrow_weathercodefullday(lat, lon, tomorrow_api_key)
        if code is not None:
            tomorrow_desc = TOMORROW_WEATHER_CODES.get(code, (f"Unknown ({code})", ""))[0]
            icon_url = get_tomorrow_icon_url(code)
            if icon_url:
                try:
                    response = requests.get(icon_url)
                    if response.status_code == 200:
                        img_data = response.content
                        img = Image.open(io.BytesIO(img_data)).resize((48, 48))
                        tomorrow_icon_img = ImageTk.PhotoImage(img)
                except Exception as e:
                    print(f"Tomorrow.io icon error: {e}")
    else:
        om_current = "Could not get coordinates for Open-Meteo."
    # Fill text areas
    current_text.config(state='normal')
    current_text.delete(1.0, tk.END)
    current_text.insert(tk.END, f"--- Visual Crossing ---\n{vc_current}\n--- Open-Meteo ---\n{om_current}")
    if tomorrow_desc:
        current_text.insert(tk.END, f"\n--- Tomorrow.io ---\nWeather: {tomorrow_desc}")
    current_text.config(state='disabled')
    # Show icon in map_panel (or create a new label for icon)
    if tomorrow_icon_img:
        map_panel.image = tomorrow_icon_img
        map_panel.config(image=tomorrow_icon_img)
    forecast_text.config(state='normal')
    forecast_text.delete(1.0, tk.END)
    forecast_text.insert(tk.END, f"{vc_forecast}")
    forecast_text.config(state='disabled')
    alerts_text.config(state='normal')
    alerts_text.delete(1.0, tk.END)
    alerts_text.insert(tk.END, f"{vc_alerts}")
    alerts_text.config(state='disabled')
    # Update map panel asynchronously
    def update_map():
        if lat is not None and lon is not None:
            layer = layer_var.get()
            zoom = int(zoom_var.get())
            layer_code = tomorrow_layers.get(layer, None)
            # Get Yandex base map URL
            yandex_url = (
                f"https://static-maps.yandex.ru/1.x/?ll={lon},{lat}&size=450,450&z={zoom}&l=map&pt={lon},{lat},pm2rdm&lang=en_US"
            )
            # Get Tomorrow.io overlay URL (if selected)
            overlay_url = None
            if tomorrow_api_key and layer_code:
                import math
                def latlon_to_tile(lat, lon, zoom):
                    lat_rad = math.radians(lat)
                    n = 2.0 ** zoom
                    x_tile = int((lon + 180.0) / 360.0 * n)
                    y_tile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
                    return x_tile, y_tile
                x_tile, y_tile = latlon_to_tile(lat, lon, zoom)
                overlay_url = f"https://api.tomorrow.io/v4/map/tile/{zoom}/{x_tile}/{y_tile}/{layer_code}/now.png?apikey={tomorrow_api_key}"
            def get_image(url):
                try:
                    response = requests.get(url)
                    if response.status_code == 200 and response.headers.get('Content-Type', '').startswith('image/png'):
                        return Image.open(io.BytesIO(response.content)).convert('RGBA')
                except Exception as e:
                    print(f"Image download error: {e}")
                return None
            # Download base map
            base_img = get_image(yandex_url)
            # Download overlay if needed
            overlay_img = get_image(overlay_url) if overlay_url else None
            # Composite overlay on base map
            final_img = None
            if base_img and overlay_img:
                # Resize overlay to match base map if needed
                try:
                    resample = Image.Resampling.LANCZOS
                except AttributeError:
                    resample = Image.LANCZOS
                overlay_img = overlay_img.resize(base_img.size, resample)
                final_img = base_img.copy()
                final_img.alpha_composite(overlay_img)
            elif base_img:
                final_img = base_img
            elif overlay_img:
                final_img = overlay_img
            # Display result
            if final_img:
                tk_img = ImageTk.PhotoImage(final_img)
                map_panel.config(image=tk_img, text='')
                map_panel.image = tk_img
            else:
                map_panel.config(image='', text='Map not available (download/content error)')
        else:
            map_panel.config(image='', text='Map not available (no coordinates)')
    threading.Thread(target=update_map, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Weatherite")
    root.state('zoomed')  # Fullscreen on Windows

    main_frame = ttk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Notebook for tabs
    notebook = ttk.Notebook(main_frame)
    notebook.pack(fill=tk.BOTH, expand=True)

    # --- Weather Tab ---
    weather_tab = ttk.Frame(notebook)
    notebook.add(weather_tab, text="Weather")

    top_frame = ttk.Frame(weather_tab)
    top_frame.pack(fill=tk.X, pady=5)

    city_label = ttk.Label(top_frame, text="Enter city name:")
    city_label.pack(side=tk.LEFT)
    city_entry = ttk.Entry(top_frame, width=30)
    city_entry.pack(side=tk.LEFT, padx=5)
    def use_current_location():
        try:
            resp = requests.get("http://ip-api.com/json", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                lat = data.get("lat")
                lon = data.get("lon")
                city = data.get("city", "")
                if lat is not None and lon is not None:
                    city_entry.delete(0, tk.END)
                    city_entry.insert(0, city)
                    city_entry.lat = lat
                    city_entry.lon = lon
                    messagebox.showinfo("Location", f"Using current location: {city} ({lat}, {lon})")
                else:
                    messagebox.showerror("Location Error", "Could not get location coordinates.")
            else:
                messagebox.showerror("Location Error", "Could not get location.")
        except Exception as e:
            messagebox.showerror("Location Error", f"Error: {e}")
    use_loc_btn = ttk.Button(top_frame, text="Use Current Location", command=use_current_location)
    use_loc_btn.pack(side=tk.LEFT, padx=5)

    units_var = tk.StringVar(value='Metric')
    units_frame = ttk.Frame(top_frame)
    units_frame.pack(side=tk.LEFT, padx=10)
    metric_radio = ttk.Radiobutton(units_frame, text="Metric", variable=units_var, value='Metric')
    metric_radio.pack(side=tk.LEFT)
    imperial_radio = ttk.Radiobutton(units_frame, text="Imperial", variable=units_var, value='Imperial')
    imperial_radio.pack(side=tk.LEFT)

    # Add forecast dropdown
    forecast_var = tk.StringVar(value='3-Day')
    forecast_options = [
        ('3-Day', '3day'),
        ('5-Day', '5day'),
        ('1 Hour', '1hour'),
        ('12 Hour', '12hour'),
        ('24 Hour', '24hour'),
        ('Week', 'week'),
    ]
    forecast_frame = ttk.Frame(top_frame)
    forecast_frame.pack(side=tk.LEFT, padx=10)
    ttk.Label(forecast_frame, text="Forecast:").pack(side=tk.LEFT)
    forecast_dropdown = ttk.Combobox(
        forecast_frame,
        textvariable=forecast_var,
        values=[text for text, value in forecast_options],
        state="readonly",
        width=10
    )
    forecast_dropdown.pack(side=tk.LEFT)
    forecast_dropdown.set(forecast_options[0][0])

    tomorrow_layers = {
    "None": None,
    "Precipitation Intensity": "precipitationIntensity",
    "Temperature": "temperature",
    "Wind Speed": "windSpeed",
    "Cloud Cover": "cloudCover",
    "Pressure": "pressure",
    "Wind Direction": "windDirection",
    "Visibility": "visibility",
    "Thunderstorm Probability": "thunderstormProbability",
    "Dew Point": "dewPoint",
    "Humidity": "humidity",
    }

    tomorrow_layers2 = [
        "None",
        "Precipitation Intensity",
        "Temperature",
        "Wind Speed",
        "Cloud Cover",
        "Pressure",
        "Wind Direction",
        "Visibility",
        "Thunderstorm Probability",
        "Dew Point",
        "Humidity",
    ]

    # Add layer selector dropdown for Tomorrow.io overlays
    layer_var = tk.StringVar(value="None")
    layer_frame = ttk.Frame(top_frame)
    layer_frame.pack(side=tk.LEFT, padx=10)
    ttk.Label(layer_frame, text="Map Layer:").pack(side=tk.LEFT)
    layer_dropdown = ttk.Combobox(
        layer_frame,
        textvariable=layer_var,
        values=tomorrow_layers2,
        state="readonly",
        width=12
    )
    layer_dropdown.pack(side=tk.LEFT)
    layer_dropdown.set(tomorrow_layers2[0])

    # Add zoom level dropdown
    zoom_var = tk.IntVar(value=10)
    zoom_frame = ttk.Frame(top_frame)
    zoom_frame.pack(side=tk.LEFT, padx=10)
    ttk.Label(zoom_frame, text="Zoom:").pack(side=tk.LEFT)
    zoom_levels = [str(z) for z in range(5, 16)]
    zoom_dropdown = ttk.Combobox(
        zoom_frame,
        textvariable=zoom_var,
        values=zoom_levels,
        state="readonly",
        width=3
    )
    zoom_dropdown.pack(side=tk.LEFT)
    zoom_dropdown.set(str(zoom_var.get()))

    search_btn = ttk.Button(top_frame, text="Get Weather", command=show_weather)
    search_btn.pack(side=tk.LEFT, padx=10)

    # Area frames
    area_frame = ttk.Frame(weather_tab)
    area_frame.pack(fill=tk.BOTH, expand=True)

    current_label = ttk.Label(area_frame, text="Current Weather", font=("Segoe UI", 14, "bold"))
    current_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
    forecast_label = ttk.Label(area_frame, text="Forecast", font=("Segoe UI", 14, "bold"))
    forecast_label.grid(row=0, column=1, sticky="w", padx=5, pady=5)
    alerts_label = ttk.Label(area_frame, text="Weather Alerts", font=("Segoe UI", 14, "bold"))
    alerts_label.grid(row=0, column=2, sticky="w", padx=5, pady=5)
    map_label = ttk.Label(area_frame, text="Weather Map", font=("Segoe UI", 14, "bold"))
    map_label.grid(row=0, column=3, sticky="w", padx=5, pady=5)

    current_text = scrolledtext.ScrolledText(area_frame, width=40, height=30, state='disabled')
    current_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
    forecast_text = scrolledtext.ScrolledText(area_frame, width=40, height=30, state='disabled')
    forecast_text.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
    alerts_text = scrolledtext.ScrolledText(area_frame, width=40, height=30, state='disabled')
    alerts_text.grid(row=1, column=2, sticky="nsew", padx=5, pady=5)
    map_panel = ttk.Label(area_frame, text='Weather map will appear here', anchor='center')
    map_panel.grid(row=1, column=3, sticky="nsew", padx=5, pady=5)

    # Add API attributions
    attribution_tomorrow = ttk.Label(area_frame, text='Powered by Tomorrow.io', font=("Segoe UI", 10, "italic"))
    attribution_tomorrow.grid(row=2, column=3, sticky="se", padx=5, pady=2)
    attribution_yandex = ttk.Label(area_frame, text='Map data © Yandex/Tomorrow.io', font=("Segoe UI", 10, "italic"))
    attribution_yandex.grid(row=2, column=2, sticky="se", padx=5, pady=2)
    attribution_openmeteo = ttk.Label(area_frame, text='Weather data © Open-Meteo', font=("Segoe UI", 10, "italic"))
    attribution_openmeteo.grid(row=2, column=0, sticky="sw", padx=5, pady=2)
    # Visual Crossing attribution as clickable link
    def open_visualcrossing():
        webbrowser.open_new("https://www.visualcrossing.com/")
    attribution_visualcrossing = ttk.Label(area_frame, text='Weather Data Provided by Visual Crossing', font=("Segoe UI", 10, "italic"), foreground="#1976D2", cursor="hand2")
    attribution_visualcrossing.grid(row=2, column=1, sticky="sw", padx=5, pady=2)
    attribution_visualcrossing.bind("<Button-1>", lambda e: open_visualcrossing())

    area_frame.columnconfigure(0, weight=1)
    area_frame.columnconfigure(1, weight=1)
    area_frame.columnconfigure(2, weight=1)
    area_frame.columnconfigure(3, weight=1)
    area_frame.rowconfigure(1, weight=1)


    # --- Historical Data Tab ---
    historical_tab = ttk.Frame(notebook)
    notebook.add(historical_tab, text="Historical Data")

    hist_top_frame = ttk.Frame(historical_tab)
    hist_top_frame.pack(fill=tk.X, pady=5)

    hist_city_label = ttk.Label(hist_top_frame, text="City:")
    hist_city_label.pack(side=tk.LEFT)
    hist_city_entry = ttk.Entry(hist_top_frame, width=30)
    hist_city_entry.pack(side=tk.LEFT, padx=5)

    hist_units_var = tk.StringVar(value='Metric')
    hist_units_frame = ttk.Frame(hist_top_frame)
    hist_units_frame.pack(side=tk.LEFT, padx=10)
    hist_metric_radio = ttk.Radiobutton(hist_units_frame, text="Metric", variable=hist_units_var, value='Metric')
    hist_metric_radio.pack(side=tk.LEFT)
    hist_imperial_radio = ttk.Radiobutton(hist_units_frame, text="Imperial", variable=hist_units_var, value='Imperial')
    hist_imperial_radio.pack(side=tk.LEFT)

    # Date range pickers
    hist_start_label = ttk.Label(hist_top_frame, text="Start Date:")
    hist_start_label.pack(side=tk.LEFT, padx=5)
    if DateEntry:
        hist_start_entry = DateEntry(hist_top_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='y-mm-dd')
        hist_end_entry = DateEntry(hist_top_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='y-mm-dd')
    else:
        hist_start_entry = ttk.Entry(hist_top_frame, width=12)
        hist_end_entry = ttk.Entry(hist_top_frame, width=12)
    hist_start_entry.pack(side=tk.LEFT, padx=5)
    hist_end_label = ttk.Label(hist_top_frame, text="End Date:")
    hist_end_label.pack(side=tk.LEFT, padx=5)
    hist_end_entry.pack(side=tk.LEFT, padx=5)

    # Preset dropdown
    hist_preset_var = tk.StringVar(value='Custom')
    hist_preset_options = ['Custom', 'Last 7 Days', 'Last 30 Days', 'This Month']
    hist_preset_dropdown = ttk.Combobox(hist_top_frame, textvariable=hist_preset_var, values=hist_preset_options, state="readonly", width=12)
    hist_preset_dropdown.pack(side=tk.LEFT, padx=5)

    def set_preset_dates():
        import datetime as dt
        today = dt.date.today()
        if hist_preset_var.get() == 'Last 7 Days':
            start = today - dt.timedelta(days=6)
            end = today
        elif hist_preset_var.get() == 'Last 30 Days':
            start = today - dt.timedelta(days=29)
            end = today
        elif hist_preset_var.get() == 'This Month':
            start = today.replace(day=1)
            end = today
        else:
            return
        if DateEntry:
            hist_start_entry.set_date(start)
            hist_end_entry.set_date(end)
        else:
            hist_start_entry.delete(0, tk.END)
            hist_start_entry.insert(0, str(start))
            hist_end_entry.delete(0, tk.END)
            hist_end_entry.insert(0, str(end))
    hist_preset_dropdown.bind('<<ComboboxSelected>>', lambda e: set_preset_dates())

    hist_search_btn = ttk.Button(hist_top_frame, text="Get Historical Weather")
    hist_search_btn.pack(side=tk.LEFT, padx=10)

    hist_area_frame = ttk.Frame(historical_tab)
    hist_area_frame.pack(fill=tk.BOTH, expand=True)

    hist_text = scrolledtext.ScrolledText(hist_area_frame, width=80, height=20, state='disabled')
    hist_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Chart button
    hist_chart_btn = ttk.Button(hist_area_frame, text="Show Chart")
    hist_chart_btn.pack(side=tk.LEFT, padx=5, pady=5)

    def show_historical_weather():
        city = hist_city_entry.get()
        units = hist_units_var.get()
        start_date = hist_start_entry.get()
        end_date = hist_end_entry.get()
        api_key = "GD85JQAPJ8T44X8VKURGLFFD9"  # Visual Crossing API key
        if not city or not start_date or not end_date:
            messagebox.showerror("Error", "Please enter a city and select start/end dates.")
            return
        hist_text.config(state='normal')
        hist_text.delete(1.0, tk.END)
        hist_text.insert(tk.END, "Loading historical weather...\n")
        def fetch_and_display():
            days = get_historical_weather_range_visualcrossing(city, api_key, units, start_date, end_date)
            summary = format_historical_stats(days, units, city, start_date, end_date)
            hist_text.config(state='normal')
            hist_text.delete(1.0, tk.END)
            hist_text.insert(tk.END, summary)
            # List daily data
            for d in days:
                date = d.get('datetime', '')
                tempmax = d.get('tempmax', '')
                tempmin = d.get('tempmin', '')
                precip = d.get('precip', '')
                hist_text.insert(tk.END, f"{date}: Max: {tempmax}, Min: {tempmin}, Precip: {precip}\n")
            hist_text.config(state='disabled')
            # Store for chart
            hist_area_frame.days = days
        threading.Thread(target=fetch_and_display, daemon=True).start()
    hist_search_btn.config(command=show_historical_weather)

    def show_chart():
        days = getattr(hist_area_frame, 'days', None)
        if not days or not plt:
            messagebox.showerror("Error", "No data or matplotlib not installed.")
            return
        dates = [d.get('datetime') for d in days]
        tempmaxs = [d.get('tempmax') for d in days]
        tempmins = [d.get('tempmin') for d in days]
        fig = plt.Figure(figsize=(6,3), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(dates, tempmaxs, label='Max Temp')
        ax.plot(dates, tempmins, label='Min Temp')
        ax.set_xlabel('Date')
        ax.set_ylabel('Temperature')
        ax.set_title('Temperature Trend')
        ax.legend()
        # Remove previous chart
        for child in hist_area_frame.winfo_children():
            if isinstance(child, FigureCanvasTkAgg):
                child.get_tk_widget().destroy()
        canvas = FigureCanvasTkAgg(fig, master=hist_area_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    hist_chart_btn.config(command=show_chart)

    sv_ttk.set_theme("dark")

    # --- Weather News & Radar Tab ---
    news_tab = ttk.Frame(notebook)
    notebook.add(news_tab, text="Weather News & Radar")

    news_area_frame = ttk.Frame(news_tab)
    news_area_frame.pack(fill=tk.BOTH, expand=True)

    # News headlines section
    news_label = ttk.Label(news_area_frame, text="Latest Weather News", font=("Segoe UI", 14, "bold"))
    news_label.pack(anchor="w", padx=5, pady=5)
    news_text = scrolledtext.ScrolledText(news_area_frame, width=60, height=15, state='disabled')
    news_text.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)

    # Radar section
    radar_label = ttk.Label(news_area_frame, text="Live Radar Map", font=("Segoe UI", 14, "bold"))
    radar_label.pack(anchor="w", padx=5, pady=5)
    radar_img_label = ttk.Label(news_area_frame, text="Radar map will appear here", anchor="center")
    radar_img_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def fetch_weather_news():
        """Fetch weather news headlines safely (UI updates on main thread)."""
        def set_message(msg: str):
            news_text.config(state='normal')
            news_text.delete(1.0, tk.END)
            news_text.insert(tk.END, msg)
            news_text.config(state='disabled')

        try:
            import feedparser  # type: ignore
        except ImportError:
            root.after(0, lambda: set_message("feedparser not installed. Install with: pip install feedparser"))
            return

        url = "https://weather.com/rss"

        def worker():
            try:
                feed = feedparser.parse(url)
                headlines = []
                for entry in getattr(feed, 'entries', [])[:10]:
                    title = getattr(entry, 'title', 'No Title')
                    link = getattr(entry, 'link', '')
                    headlines.append(f"- {title}\n{link}\n")
                msg = "\n".join(headlines) if headlines else "No news found." if headlines is not None else "No news found."
            except Exception as e:
                msg = f"Error fetching news: {e}"
            root.after(0, lambda m=msg: set_message(m))

        threading.Thread(target=worker, daemon=True).start()

    def fetch_radar_image():
        """Fetch simple radar tile and update UI safely."""
        radar_url = "https://tilecache.rainviewer.com/v2/radar/nowcast/0/0/0/2/256.png"
        try:
            response = requests.get(radar_url, timeout=15)
            if response.status_code == 200 and response.headers.get('Content-Type', '').startswith('image'):
                try:
                    img_data = response.content
                    img = Image.open(io.BytesIO(img_data)).resize((512, 512))
                    tk_img = ImageTk.PhotoImage(img)
                    root.after(0, lambda i=tk_img: (radar_img_label.config(image=i, text=''), setattr(radar_img_label, 'image', i)))
                except Exception as e:
                    root.after(0, lambda: radar_img_label.config(image='', text=f'Radar decode error: {e}'))
            else:
                root.after(0, lambda: radar_img_label.config(image='', text='Radar map not available.'))
        except Exception as e:
            root.after(0, lambda: radar_img_label.config(image='', text=f'Radar error: {e}'))

    threading.Thread(target=fetch_weather_news, daemon=True).start()
    threading.Thread(target=fetch_radar_image, daemon=True).start()

    # --- Tornado History Tab (Added) ---
    tornado_tab = ttk.Frame(notebook)
    notebook.add(tornado_tab, text="Tornado History")

    tornado_top = ttk.Frame(tornado_tab)
    tornado_top.pack(fill=tk.X, pady=5)

    ttk.Label(tornado_top, text="City:").pack(side=tk.LEFT)
    tornado_city_entry = ttk.Entry(tornado_top, width=25)
    tornado_city_entry.pack(side=tk.LEFT, padx=4)

    # Date selectors
    ttk.Label(tornado_top, text="Start Date:").pack(side=tk.LEFT, padx=4)
    if DateEntry:
        tornado_start_entry = DateEntry(tornado_top, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='y-mm-dd')
        tornado_end_entry = DateEntry(tornado_top, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='y-mm-dd')
    else:
        tornado_start_entry = ttk.Entry(tornado_top, width=12)
        tornado_end_entry = ttk.Entry(tornado_top, width=12)
    tornado_start_entry.pack(side=tk.LEFT, padx=2)
    ttk.Label(tornado_top, text="End Date:").pack(side=tk.LEFT, padx=4)
    tornado_end_entry.pack(side=tk.LEFT, padx=2)

    # Radius selector (kilometers)
    ttk.Label(tornado_top, text="Radius (km):").pack(side=tk.LEFT, padx=4)
    tornado_radius_var = tk.DoubleVar(value=75.0)
    tornado_radius_spin = ttk.Spinbox(tornado_top, from_=10.0, to=500.0, increment=5.0, width=7, textvariable=tornado_radius_var)
    tornado_radius_spin.pack(side=tk.LEFT)

    tornado_fetch_btn = ttk.Button(tornado_top, text="Load Tornado Data")
    tornado_fetch_btn.pack(side=tk.LEFT, padx=8)

    # Show paths checkbox
    tornado_show_paths_var = tk.BooleanVar(value=True)
    tornado_paths_chk = ttk.Checkbutton(tornado_top, text="Show Paths", variable=tornado_show_paths_var)
    tornado_paths_chk.pack(side=tk.LEFT, padx=4)

    # (Removed ArcGIS / IEM options – NOAA SWDI is now sole data source)

    # Area frame
    tornado_area = ttk.Frame(tornado_tab)
    tornado_area.pack(fill=tk.BOTH, expand=True)

    tornado_output = scrolledtext.ScrolledText(tornado_area, height=12, state='disabled')
    tornado_output.pack(fill=tk.X, padx=5, pady=5)

    tornado_map_container = ttk.Frame(tornado_area)
    tornado_map_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    tornado_map_label = ttk.Label(tornado_map_container, text="Tornado map will appear here", anchor='center')
    tornado_map_label.pack(fill=tk.BOTH, expand=True)

    # Color mapping for EF scale
    EF_COLORS = {
        'U': "#1900FF",
        '0': "#00ffff",
        '1': "#48ff00",
        '2': "#fffb00",
        '3': "#ffae00",
        '4': "#cc0000",
        '5': "#FF00D4",
        'UNK': '#888888'
    }

    def log_tornado(text, replace=False):
        # Ensure UI updates occur on main thread
        def _do():
            tornado_output.config(state='normal')
            if replace:
                tornado_output.delete(1.0, tk.END)
            tornado_output.insert(tk.END, text)
            tornado_output.see(tk.END)
            tornado_output.config(state='disabled')
        try:
            root.after(0, _do)
        except Exception:
            # Fallback (in case root not yet defined in some context)
            _do()

    def haversine_km(lat1, lon1, lat2, lon2):
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    # (Removed fetch_tornado_reports – IEM LSR no longer used)

    def fetch_tornado_tracks(city, start_date, end_date, radius_km):
        """Fetch tornado tracks (begin/end points) from NOAA SWDI and filter by km radius (start or end within radius)."""
        lat, lon = get_coordinates(city)
        if lat is None or lon is None:
            return None, f"Unable to geocode city '{city}' for tracks."
        lat_buffer_deg = radius_km / 111.0
        cos_lat = max(math.cos(math.radians(lat)), 0.0001)
        lon_buffer_deg = radius_km / (111.320 * cos_lat)
        minLat = lat - lat_buffer_deg
        maxLat = lat + lat_buffer_deg
        minLon = lon - lon_buffer_deg
        maxLon = lon + lon_buffer_deg
        base_url = f"https://www.ncdc.noaa.gov/swdiws/csv/tornadoes/{start_date}/{end_date}?bbox={minLon},{minLat},{maxLon},{maxLat}"
        try:
            resp = requests.get(base_url, timeout=20)
            if resp.status_code != 200:
                return None, f"SWDI tracks API error {resp.status_code}."
            lines = resp.text.splitlines()
            if not lines:
                return [], None
            header = lines[0].split(',')
            def idx(col):
                try:
                    return header.index(col)
                except ValueError:
                    return -1
            idx_BEGIN_LAT = idx('BEGIN_LAT')
            idx_BEGIN_LON = idx('BEGIN_LON')
            idx_END_LAT = idx('END_LAT')
            idx_END_LON = idx('END_LON')
            idx_F = idx('TOR_F_SCALE')
            idx_DATE = idx('BEGIN_DATE')
            tracks = []
            for line in lines[1:]:
                parts = line.split(',')
                try:
                    if min(idx_BEGIN_LAT, idx_BEGIN_LON, idx_END_LAT, idx_END_LON) < 0:
                        continue
                    slat = float(parts[idx_BEGIN_LAT])
                    slon = float(parts[idx_BEGIN_LON])
                    elat = float(parts[idx_END_LAT])
                    elon = float(parts[idx_END_LON])
                    ef = parts[idx_F] if idx_F >= 0 and idx_F < len(parts) else 'UNK'
                    date = parts[idx_DATE] if idx_DATE >= 0 and idx_DATE < len(parts) else ''
                    if (haversine_km(lat, lon, slat, slon) <= radius_km) or (haversine_km(lat, lon, elat, elon) <= radius_km):
                        tracks.append({
                            'start_lat': slat,
                            'start_lon': slon,
                            'end_lat': elat,
                            'end_lon': elon,
                            'ef': ef if ef else 'UNK',
                            'date': date,
                            'city_lat': lat,
                            'city_lon': lon
                        })
                except Exception:
                    continue
            return tracks, None
        except Exception as e:
            return None, f"Error fetching tracks: {e}"

    # (Removed fetch_tornado_arcgis – ArcGIS dataset no longer used)

    def synthesize_reports_from_tracks(tracks):
        """Create point-style 'reports' from NOAA track start points.
        Each synthetic report mimics the old IEM structure for UI/log reuse."""
        reports = []
        for t in tracks or []:
            try:
                reports.append({
                    'lat': t['start_lat'],
                    'lon': t['start_lon'],
                    'valid': t.get('date'),
                    'magnitude': t.get('ef'),
                    'city_lat': t.get('city_lat'),
                    'city_lon': t.get('city_lon'),
                    'wfo': 'NOAA',
                    'remark': 'Track start point'
                })
            except Exception:
                continue
        return reports

    def plot_tornado_reports(city, reports, tracks=None):
        if not plt:
            log_tornado("matplotlib not installed. Install it for map visualization.\n", replace=False)
            return
        # Clear previous figure widgets
        for child in tornado_map_container.winfo_children():
            if isinstance(child, FigureCanvasTkAgg):
                child.get_tk_widget().destroy()
        if (not reports) and (not tracks):
            tornado_map_label.config(text="No tornado data in range.")
            return
        tornado_map_label.config(text="")
        lats = [r['lat'] for r in reports] if reports else []
        lons = [r['lon'] for r in reports] if reports else []
        if tracks:
            lats.extend([t['start_lat'] for t in tracks] + [t['end_lat'] for t in tracks])
            lons.extend([t['start_lon'] for t in tracks] + [t['end_lon'] for t in tracks])
        # Determine city center using first available dataset
        if reports:
            city_lat = reports[0]['city_lat']
            city_lon = reports[0]['city_lon']
        else:
            city_lat = tracks[0]['city_lat']
            city_lon = tracks[0]['city_lon']
        pad = 0.5
        min_lat = min(lats + [city_lat]) - pad
        max_lat = max(lats + [city_lat]) + pad
        min_lon = min(lons + [city_lon]) - pad
        max_lon = max(lons + [city_lon]) + pad
        fig = plt.Figure(figsize=(6,6), dpi=100)
        ax = fig.add_subplot(111)
        ax.set_title(f"Tornado Reports near {city}")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_xlim(min_lon, max_lon)
        ax.set_ylim(min_lat, max_lat)
        # Plot city
        ax.plot(city_lon, city_lat, 'bo', label=city)
        # Plot reports (points)
        if reports:
            for r in reports:
                ef = str(r['magnitude']) if r['magnitude'] not in (None, '') else 'UNK'
                color = EF_COLORS.get(ef, '#888888')
                ax.plot(r['lon'], r['lat'], marker='o', color=color, markersize=6, alpha=0.75)
        # Plot tracks (lines)
        if tracks:
            for t in tracks:
                ef = str(t['ef']) if t['ef'] else 'UNK'
                color = EF_COLORS.get(ef, '#888888')
                ax.plot([t['start_lon'], t['end_lon']], [t['start_lat'], t['end_lat']], color=color, linewidth=2, alpha=0.9)
                ax.text(t['end_lon'], t['end_lat'], f"EF{ef}", fontsize=7, color=color)
        # Legend for EF colors
        handles = []
        import matplotlib.patches as mpatches
        for k, v in EF_COLORS.items():
            label = f"EF{k}" if k != 'UNK' else 'Unknown/Point'
            handles.append(mpatches.Patch(color=v, label=label))
        ax.legend(handles=handles, fontsize=8, loc='upper right')
        canvas = FigureCanvasTkAgg(fig, master=tornado_map_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def load_tornado_history():
        _city = tornado_city_entry.get().strip()
        _start_date = tornado_start_entry.get().strip()
        _end_date = tornado_end_entry.get().strip()
        _radius = tornado_radius_var.get()  # km
        if not _city or not _start_date or not _end_date:
            messagebox.showerror("Error", "City and date range required.")
            return
        # Removed trailing space inside f-string format spec to avoid ValueError
        log_tornado(f"Fetching NOAA tornado tracks (radius {_radius:.1f} km)...\n", replace=True)
        city = _city; start_date = _start_date; end_date = _end_date; radius = _radius  # capture
        def worker(city_=city, start_=start_date, end_=end_date, radius_=radius):
            tracks, err = fetch_tornado_tracks(city_, start_, end_, radius_)
            if err:
                log_tornado(err + "\n", replace=True)
                return
            if not tracks:
                log_tornado(f"No tornado tracks found near {city_} for given range.\n", replace=True)
                return
            reports = synthesize_reports_from_tracks(tracks)
            # Sort reports by date
            reports.sort(key=lambda r: r.get('valid') or '')
            log_tornado(f"Tracks ({len(tracks)}), Synthetic Reports ({len(reports)}):\n", replace=True)
            # Log a limited list of reports
            for r in reports[:200]:
                ef = r['magnitude'] if r['magnitude'] not in (None, '') else 'UNK'
                log_tornado(f"{r['valid']}: EF{ef} at ({r['lat']:.2f},{r['lon']:.2f}) {r['remark']}\n")
            if len(reports) > 200:
                log_tornado(f"... truncated {len(reports)-200} more synthetic reports ...\n")
            if tornado_show_paths_var.get():
                plot_tornado_reports(city_, reports, tracks)
            else:
                plot_tornado_reports(city_, reports, None)
        threading.Thread(target=worker, daemon=True).start()
    tornado_fetch_btn.config(command=load_tornado_history)

    # Helpful preset: set today and yesterday
    try:
        from datetime import date, timedelta
        today = date.today()
        yday = today - timedelta(days=1)
        if DateEntry:
            tornado_start_entry.set_date(yday)
            tornado_end_entry.set_date(today)
        else:
            tornado_start_entry.insert(0, str(yday))
            tornado_end_entry.insert(0, str(today))
    except Exception:
        pass

    # --- User Accounts & Sync Tab ---
    accounts_tab = ttk.Frame(notebook)
    notebook.add(accounts_tab, text="User Accounts & Sync")

    accounts_area_frame = ttk.Frame(accounts_tab)
    accounts_area_frame.pack(fill=tk.BOTH, expand=True)

    # Login/Register section
    login_label = ttk.Label(accounts_area_frame, text="Sign In / Register", font=("Segoe UI", 14, "bold"))
    login_label.pack(anchor="w", padx=5, pady=5)

    username_label = ttk.Label(accounts_area_frame, text="Username:")
    username_label.pack(anchor="w", padx=5)
    username_entry = ttk.Entry(accounts_area_frame, width=30)
    username_entry.pack(anchor="w", padx=5)

    password_label = ttk.Label(accounts_area_frame, text="Password:")
    password_label.pack(anchor="w", padx=5)
    password_entry = ttk.Entry(accounts_area_frame, width=30, show="*")
    password_entry.pack(anchor="w", padx=5)

    status_var = tk.StringVar(value="Not signed in")
    status_label = ttk.Label(accounts_area_frame, textvariable=status_var, font=("Segoe UI", 10, "italic"))
    status_label.pack(anchor="w", padx=5, pady=5)


    # --- GitHub OAuth (Improved: Device Flow, no embedded secret) ---
    # Why: A packaged desktop EXE cannot reliably hide a client secret. GitHub Device Flow removes the need for one.
    import webbrowser
    import threading
    import time

    GITHUB_CLIENT_ID = "Ov23lia3P7WUUFlt8GbM"  # Public ID (safe)
    GITHUB_SCOPE = "read:user user:email"
    GITHUB_DEVICE_CODE_URL = "https://github.com/login/device/code"
    GITHUB_OAUTH_TOKEN_URL = "https://github.com/login/oauth/access_token"
    GITHUB_USER_API = "https://api.github.com/user"

    GITHUB_ACCESS_TOKEN = None
    GITHUB_USER_INFO = None
    _device_poll_stop = False

    def _github_device_start():
        data = {"client_id": GITHUB_CLIENT_ID, "scope": GITHUB_SCOPE}
        try:
            r = requests.post(GITHUB_DEVICE_CODE_URL, data=data, headers={"Accept": "application/json"}, timeout=15)
            if r.status_code != 200:
                return None, f"GitHub device start error {r.status_code}"
            return r.json(), None
        except Exception as e:
            return None, f"GitHub device start exception: {e}"

    def _github_poll(device_code, interval, expires_in):
        global GITHUB_ACCESS_TOKEN, GITHUB_USER_INFO, _device_poll_stop
        deadline = time.time() + expires_in
        while time.time() < deadline and not _device_poll_stop:
            try:
                payload = {
                    "client_id": GITHUB_CLIENT_ID,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
                }
                r = requests.post(GITHUB_OAUTH_TOKEN_URL, data=payload, headers={"Accept": "application/json"}, timeout=15)
                if r.status_code != 200:
                    time.sleep(interval)
                    continue
                data = r.json()
                if 'access_token' in data:
                    GITHUB_ACCESS_TOKEN = data['access_token']
                    ui = requests.get(GITHUB_USER_API, headers={"Authorization": f"Bearer {GITHUB_ACCESS_TOKEN}", "Accept": "application/vnd.github+json"}, timeout=15)
                    if ui.status_code == 200:
                        GITHUB_USER_INFO = ui.json()
                        login = GITHUB_USER_INFO.get('login', '?')
                        root.after(0, lambda: status_var.set(f"Signed in with GitHub: {login}"))
                    else:
                        root.after(0, lambda: status_var.set("GitHub sign-in succeeded, user fetch failed."))
                    return
                error = data.get('error')
                if error == 'authorization_pending':
                    pass
                elif error == 'slow_down':
                    interval += 2
                elif error == 'expired_token':
                    root.after(0, lambda: status_var.set("GitHub code expired. Try again."))
                    return
                else:
                    if error:
                        root.after(0, lambda e=error: status_var.set(f"GitHub auth error: {e}"))
                    return
            except Exception as e:
                root.after(0, lambda: status_var.set(f"GitHub poll err: {e}"))
                return
            time.sleep(interval)
        if not GITHUB_ACCESS_TOKEN and not _device_poll_stop:
            root.after(0, lambda: status_var.set("GitHub sign-in timed out."))

    def cancel_github_login():
        global _device_poll_stop
        _device_poll_stop = True
        status_var.set("GitHub sign-in canceled.")
        cancel_btn.configure(state='disabled')
        login_button.configure(state='normal')

    def start_github_login():
        global _device_poll_stop
        _device_poll_stop = False
        status_var.set("Starting GitHub Device Flow...")
        login_button.configure(state='disabled')
        cancel_btn.configure(state='normal')
        def runner():
            info, err = _github_device_start()
            if err or not info:
                root.after(0, lambda: (status_var.set(err or "Device flow init failed"), login_button.configure(state='normal'), cancel_btn.configure(state='disabled')))
                return
            user_code = info['user_code']
            verify_uri = info['verification_uri']
            interval = info.get('interval', 5)
            expires_in = info.get('expires_in', 900)
            root.after(0, lambda: status_var.set(f"Open {verify_uri} and enter code: {user_code} (copied)"))
            try:
                webbrowser.open(verify_uri)
            except Exception:
                pass
            try:
                root.clipboard_clear(); root.clipboard_append(user_code)
            except Exception:
                pass
            _github_poll(info['device_code'], interval, expires_in)
            root.after(0, lambda: (login_button.configure(state='normal'), cancel_btn.configure(state='disabled')))
        threading.Thread(target=runner, daemon=True).start()

    login_button = ttk.Button(accounts_area_frame, text="Sign in with GitHub", command=start_github_login)
    login_button.pack(anchor='w', padx=5, pady=5)
    cancel_btn = ttk.Button(accounts_area_frame, text="Cancel GitHub Sign-In", command=cancel_github_login, state='disabled')
    cancel_btn.pack(anchor='w', padx=5, pady=2)

    root.mainloop()
