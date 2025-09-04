import requests
import tkinter as tk
from tkinter import messagebox, scrolledtext
from tkinter import ttk
import sv_ttk
from datetime import datetime
from PIL import Image, ImageTk
import io
import threading
import tempfile
import os


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
    # Tomorrow.io official icons: https://docs.tomorrow.io/reference/data-weather-codes
    # Example: https://assets.tomorrow.io/images/icons/condition/{code}.png
    # PNG icons are available for each code
    if code is not None:
        return f"https://assets.tomorrow.io/images/icons/condition/{code}.png"
    return None
# Tomorrow.io layers supported
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
}

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
            img_url = None
            if tomorrow_api_key and layer_code:
                import math
                def latlon_to_tile(lat, lon, zoom):
                    lat_rad = math.radians(lat)
                    n = 2.0 ** zoom
                    x_tile = int((lon + 180.0) / 360.0 * n)
                    y_tile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
                    return x_tile, y_tile
                x_tile, y_tile = latlon_to_tile(lat, lon, zoom)
                img_url = f"https://api.tomorrow.io/v4/map/tile/{zoom}/{x_tile}/{y_tile}/{layer_code}/now.png?apikey={tomorrow_api_key}"
            else:
                img_url = (
                    f"https://static-maps.yandex.ru/1.x/?ll={lon},{lat}&size=450,450&z={zoom}&l=map&pt={lon},{lat},pm2rdm&lang=en_US"
                )
            def try_load_image(url):
                try:
                    response = requests.get(url)
                    content_type = response.headers.get('Content-Type', '')
                    if response.status_code == 200 and content_type.startswith('image/png'):
                        img_data = response.content
                        tk_img = None
                        pil_error = None
                        tk_error = None
                        try:
                            img = Image.open(io.BytesIO(img_data))
                            img = img.resize((450, 450))
                            tk_img = ImageTk.PhotoImage(img)
                        except Exception as e:
                            pil_error = str(e)
                            print(f"PIL error: {pil_error}")
                            try:
                                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                                    tmp.write(img_data)
                                    tmp_path = tmp.name
                                tk_img = tk.PhotoImage(file=tmp_path)
                                os.unlink(tmp_path)
                            except Exception as e2:
                                tk_error = str(e2)
                                print(f"Tkinter PhotoImage error: {tk_error}")
                                tk_img = None
                        if tk_img:
                            map_panel.config(image=tk_img, text='')
                            map_panel.image = tk_img
                            return True
                        else:
                            if pil_error:
                                map_panel.config(image='', text=f'Map not available (PIL error)')
                            elif tk_error:
                                map_panel.config(image='', text=f'Map not available (Tkinter error)')
                            else:
                                map_panel.config(image='', text='Map not available (unknown image error)')
                            return False
                    else:
                        print(f"Map download error: status={response.status_code}, content_type={content_type}")
                        print(f"Response head: {response.content[:200]}")
                        return False
                except Exception as e:
                    print(f"Network error: {e}")
                    return False
            success = try_load_image(img_url)
            if not success:
                map_panel.config(image='', text='Map not available (Tomorrow.io/Yandex error)')
        else:
            map_panel.config(image='', text='Map not available (no coordinates)')
    threading.Thread(target=update_map, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Weather App")
    root.state('zoomed')  # Fullscreen on Windows

    main_frame = ttk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    top_frame = ttk.Frame(main_frame)
    top_frame.pack(fill=tk.X, pady=5)

    city_label = ttk.Label(top_frame, text="Enter city name:")
    city_label.pack(side=tk.LEFT)
    city_entry = ttk.Entry(top_frame, width=30)
    city_entry.pack(side=tk.LEFT, padx=5)

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

    # Add layer selector dropdown for Tomorrow.io overlays
    layer_var = tk.StringVar(value="None")
    layer_frame = ttk.Frame(top_frame)
    layer_frame.pack(side=tk.LEFT, padx=10)
    ttk.Label(layer_frame, text="Map Layer:").pack(side=tk.LEFT)
    layer_dropdown = ttk.Combobox(
        layer_frame,
        textvariable=layer_var,
        values=tomorrow_layers,
        state="readonly",
        width=12
    )
    layer_dropdown.pack(side=tk.LEFT)
    layer_dropdown.set(tomorrow_layers[0])

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
    area_frame = ttk.Frame(main_frame)
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
    attribution_visualcrossing = ttk.Label(area_frame, text='Weather data © Visual Crossing', font=("Segoe UI", 10, "italic"))
    attribution_visualcrossing.grid(row=2, column=1, sticky="sw", padx=5, pady=2)

    area_frame.columnconfigure(0, weight=1)
    area_frame.columnconfigure(1, weight=1)
    area_frame.columnconfigure(2, weight=1)
    area_frame.columnconfigure(3, weight=1)
    area_frame.rowconfigure(1, weight=1)

    sv_ttk.set_theme("dark")

    root.mainloop()
