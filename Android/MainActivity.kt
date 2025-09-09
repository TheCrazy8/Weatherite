package com.example.weatherapp

import android.os.Bundle
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import com.bumptech.glide.Glide
import com.google.android.gms.ads.AdRequest
import com.google.android.gms.ads.MobileAds
import com.google.android.gms.ads.AdView
import kotlinx.coroutines.*
import okhttp3.*
import org.json.JSONObject
import java.io.IOException

class MainActivity : AppCompatActivity() {
    private lateinit var cityInput: EditText
    private lateinit var unitsGroup: RadioGroup
    private lateinit var forecastSpinner: Spinner
    private lateinit var layerSpinner: Spinner
    private lateinit var zoomSpinner: Spinner
    private lateinit var searchBtn: Button
    private lateinit var currentWeather: TextView
    private lateinit var forecastWeather: TextView
    private lateinit var alertsWeather: TextView
    private lateinit var mapImage: ImageView
    private lateinit var tomorrowIconView: ImageView
    private lateinit var tomorrowDescView: TextView
    private lateinit var adView: AdView
    private lateinit var visualCrossingAttribution: TextView

    private val visualCrossingApiKey = "GD85JQAPJ8T44X8VKURGLFFD9"
    private val tomorrowApiKey = "ku1mDhkjQlc8CRZkOzXr8wZ0BjTEUInB"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

    cityInput = findViewById(R.id.cityInput)
    unitsGroup = findViewById(R.id.unitsGroup)
    forecastSpinner = findViewById(R.id.forecastSpinner)
    layerSpinner = findViewById(R.id.layerSpinner)
    zoomSpinner = findViewById(R.id.zoomSpinner)
    searchBtn = findViewById(R.id.searchBtn)
    currentWeather = findViewById(R.id.currentWeather)
    forecastWeather = findViewById(R.id.forecastWeather)
    alertsWeather = findViewById(R.id.alertsWeather)
    mapImage = findViewById(R.id.mapImage)
    tomorrowIconView = findViewById(R.id.tomorrowIconView)
    tomorrowDescView = findViewById(R.id.tomorrowDescView)
    adView = findViewById(R.id.adView)
    visualCrossingAttribution = findViewById(R.id.visualCrossingAttribution)
    visualCrossingAttribution.setTextColor(0xFF1976D2.toInt())
    visualCrossingAttribution.paint.isUnderlineText = true
    visualCrossingAttribution.setOnClickListener {
        val url = "https://www.visualcrossing.com/"
        val intent = android.content.Intent(android.content.Intent.ACTION_VIEW)
        intent.data = android.net.Uri.parse(url)
        startActivity(intent)
    }

    // Initialize Mobile Ads SDK and load banner ad
    MobileAds.initialize(this) {}
    val adRequest = AdRequest.Builder().build()
    adView.loadAd(adRequest)

        // Populate spinners
        val forecastOptions = arrayOf("3-Day", "5-Day", "1 Hour", "12 Hour", "24 Hour", "Week")
        forecastSpinner.adapter = ArrayAdapter(this, android.R.layout.simple_spinner_dropdown_item, forecastOptions)
        val layerOptions = arrayOf(
            "None", "Precipitation Intensity", "Temperature", "Wind Speed", "Cloud Cover", "Pressure", "Wind Direction", "Visibility", "Thunderstorm Probability", "Dew Point", "Humidity"
        )
        layerSpinner.adapter = ArrayAdapter(this, android.R.layout.simple_spinner_dropdown_item, layerOptions)
        val zoomOptions = (5..15).map { it.toString() }.toTypedArray()
        zoomSpinner.adapter = ArrayAdapter(this, android.R.layout.simple_spinner_dropdown_item, zoomOptions)

        searchBtn.setOnClickListener {
            val city = cityInput.text.toString()
            val units = if (unitsGroup.checkedRadioButtonId == R.id.metricRadio) "Metric" else "Imperial"
            val forecastType = forecastSpinner.selectedItem.toString()
            val layer = layerSpinner.selectedItem.toString()
            val zoom = zoomSpinner.selectedItem.toString().toInt()
            fetchWeather(city, units, forecastType, layer, zoom)
        }
    }

    private fun fetchWeather(city: String, units: String, forecastType: String, layer: String, zoom: Int) {
        CoroutineScope(Dispatchers.IO).launch {
            try {
                // 1. Get coordinates
                val (lat, lon) = getCoordinates(city)
                // 2. Get weather data
                val vcWeather = getWeatherVisualCrossing(city, units, forecastType)
                val omWeather = getWeatherOpenMeteo(lat, lon, units)
                val tomorrowResult = getTomorrowWeatherCodeAndIcon(lat, lon)
                // 3. Get map image
                val mapUrl = getYandexMapUrl(lat, lon, zoom)
                // 4. Get overlay image (Tomorrow.io)
                val overlayUrl = getTomorrowOverlayUrl(lat, lon, zoom, layer)

                withContext(Dispatchers.Main) {
                    currentWeather.text = "--- Visual Crossing ---\n${vcWeather.current}\n--- Open-Meteo ---\n${omWeather}"
                    forecastWeather.text = vcWeather.forecast
                    alertsWeather.text = vcWeather.alerts
                    // Load base map
                    Glide.with(this@MainActivity).load(mapUrl).into(mapImage)
                    // Overlay (if available)
                    if (overlayUrl != null) {
                        Glide.with(this@MainActivity).load(overlayUrl).into(mapImage)
                    }
                    // Tomorrow.io icon and desc
                    if (tomorrowResult != null) {
                        tomorrowDescView.text = tomorrowResult.desc
                        if (tomorrowResult.iconUrl != null) {
                            Glide.with(this@MainActivity).load(tomorrowResult.iconUrl).into(tomorrowIconView)
                        } else {
                            tomorrowIconView.setImageDrawable(null)
                        }
                    } else {
                        tomorrowDescView.text = ""
                        tomorrowIconView.setImageDrawable(null)
                    }
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    Toast.makeText(this@MainActivity, "Error: ${e.message}", Toast.LENGTH_LONG).show()
                }
            }
        }
    }

    private suspend fun getCoordinates(city: String): Pair<Double, Double> {
        val url = "https://geocoding-api.open-meteo.com/v1/search?name=${city}&count=1"
        val client = OkHttpClient()
        val request = Request.Builder().url(url).build()
        val response = client.newCall(request).execute()
        val body = response.body?.string() ?: return Pair(0.0, 0.0)
        val json = JSONObject(body)
        val results = json.optJSONArray("results")
        if (results != null && results.length() > 0) {
            val obj = results.getJSONObject(0)
            val lat = obj.getDouble("latitude")
            val lon = obj.getDouble("longitude")
            return Pair(lat, lon)
        }
        return Pair(0.0, 0.0)
    }

    private suspend fun getWeatherVisualCrossing(city: String, units: String, forecastType: String): WeatherResult {
        val unitGroup = if (units == "Imperial") "us" else "metric"
        val includeParam = "current,days,alerts,hours"
        val url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/${city}?unitGroup=${unitGroup}&key=${visualCrossingApiKey}&include=${includeParam}"
        val client = OkHttpClient()
        val request = Request.Builder().url(url).build()
        val response = client.newCall(request).execute()
        val body = response.body?.string() ?: return WeatherResult("City not found or API error.", "", "")
        val json = JSONObject(body)
        // Current
        val current = json.optJSONObject("currentConditions") ?: JSONObject()
        val weather = current.optString("conditions", "N/A")
        val temp = current.optString("temp", "N/A")
        val feelsLike = current.optString("feelslike", "N/A")
        val humidity = current.optString("humidity", "N/A")
        val windSpeed = current.optString("windspeed", "N/A")
        val precip = current.optString("precip", "N/A")
        val pressure = current.optString("pressure", "N/A")
        val uvIndex = current.optString("uvindex", "N/A")
        val visibility = current.optString("visibility", "N/A")
        val sunrise = current.optString("sunrise", "N/A")
        val sunset = current.optString("sunset", "N/A")
        val tempUnit = if (units == "Imperial") "°F" else "°C"
        val speedUnit = if (units == "Imperial") "mph" else "km/h"
        val precipUnit = if (units == "Imperial") "in" else "mm"
        val pressureUnit = if (units == "Imperial") "inHg" else "hPa"
        val visUnit = if (units == "Imperial") "mi" else "km"
        val now = java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(java.util.Date())
        var outputCurrent = "Current Date & Time: $now\nWeather in $city: $weather\nTemperature: $temp$tempUnit (Feels like: $feelsLike$tempUnit)\nHumidity: $humidity%\nWind Speed: $windSpeed $speedUnit\nPrecipitation: $precip $precipUnit\nPressure: $pressure $pressureUnit\nUV Index: $uvIndex\nVisibility: $visibility $visUnit\nSunrise: $sunrise\nSunset: $sunset\n"
        // Forecast
        var outputForecast = "Forecast:\n"
        val days = json.optJSONArray("days") ?: return WeatherResult(outputCurrent, "No forecast data.", "")
        when (forecastType) {
            "3-Day" -> {
                outputForecast += "3-Day Forecast:\n"
                for (i in 0 until minOf(3, days.length())) {
                    val day = days.getJSONObject(i)
                    val date = day.optString("datetime", "N/A")
                    val desc = day.optString("description", "N/A")
                    val tempmax = day.optString("tempmax", "N/A")
                    val tempmin = day.optString("tempmin", "N/A")
                    outputForecast += "$date: $desc\n  Max: $tempmax$tempUnit, Min: $tempmin$tempUnit\n"
                }
            }
            "5-Day" -> {
                outputForecast += "5-Day Forecast:\n"
                for (i in 0 until minOf(5, days.length())) {
                    val day = days.getJSONObject(i)
                    val date = day.optString("datetime", "N/A")
                    val desc = day.optString("description", "N/A")
                    val tempmax = day.optString("tempmax", "N/A")
                    val tempmin = day.optString("tempmin", "N/A")
                    outputForecast += "$date: $desc\n  Max: $tempmax$tempUnit, Min: $tempmin$tempUnit\n"
                }
            }
            "Week" -> {
                outputForecast += "7-Day Forecast:\n"
                for (i in 0 until minOf(7, days.length())) {
                    val day = days.getJSONObject(i)
                    val date = day.optString("datetime", "N/A")
                    val desc = day.optString("description", "N/A")
                    val tempmax = day.optString("tempmax", "N/A")
                    val tempmin = day.optString("tempmin", "N/A")
                    outputForecast += "$date: $desc\n  Max: $tempmax$tempUnit, Min: $tempmin$tempUnit\n"
                }
            }
            "1 Hour", "12 Hour", "24 Hour" -> {
                val hours = json.optJSONArray("hours") ?: return WeatherResult(outputCurrent, outputForecast, "")
                val count = when (forecastType) {
                    "1 Hour" -> 1
                    "12 Hour" -> 12
                    "24 Hour" -> 24
                    else -> 1
                }
                outputForecast += "Next $count Hours Forecast:\n"
                for (i in 0 until minOf(count, hours.length())) {
                    val hour = hours.getJSONObject(i)
                    val time = hour.optString("datetime", "N/A")
                    val tempH = hour.optString("temp", "N/A")
                    val descH = hour.optString("conditions", "N/A")
                    val feelslikeH = hour.optString("feelslike", "N/A")
                    val humidityH = hour.optString("humidity", "N/A")
                    val windH = hour.optString("windspeed", "N/A")
                    outputForecast += "$time: $descH, Temp: $tempH$tempUnit, Feels like: $feelslikeH$tempUnit, Humidity: $humidityH%, Wind: $windH $speedUnit\n"
                }
            }
        }
        // Alerts
        var outputAlerts = ""
        val alerts = json.optJSONArray("alerts")
        if (alerts != null && alerts.length() > 0) {
            outputAlerts += "Weather Alerts:\n"
            for (i in 0 until alerts.length()) {
                val alert = alerts.getJSONObject(i)
                val title = alert.optString("event", "Alert")
                val desc = alert.optString("description", "")
                val starts = alert.optString("onset", "N/A")
                val ends = alert.optString("ends", "N/A")
                outputAlerts += "$title:\n  Starts: $starts\n  Ends: $ends\n  $desc\n"
            }
        } else {
            outputAlerts += "No active weather alerts.\n"
        }
        return WeatherResult(outputCurrent, outputForecast, outputAlerts)
    }

    private suspend fun getWeatherOpenMeteo(lat: Double, lon: Double, units: String): String {
        val url = "https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true&hourly=cape,wind_speed_10m,wind_speed_80m,wind_speed_100m&daily=temperature_2m_max,temperature_2m_min,weathercode&timezone=auto"
        val client = OkHttpClient()
        val request = Request.Builder().url(url).build()
        val response = client.newCall(request).execute()
        val body = response.body?.string() ?: return "API error or location not found."
        val json = JSONObject(body)
        val cape = json.optJSONObject("hourly")?.optJSONArray("cape")?.optString(0, "N/A") ?: "N/A"
        val wind10m = json.optJSONObject("hourly")?.optJSONArray("wind_speed_10m")?.optString(0, "N/A") ?: "N/A"
        val wind80m = json.optJSONObject("hourly")?.optJSONArray("wind_speed_80m")?.optString(0, "N/A") ?: "N/A"
        val wind100m = json.optJSONObject("hourly")?.optJSONArray("wind_speed_100m")?.optString(0, "N/A") ?: "N/A"
        val speedUnit = if (units == "Imperial") "mph" else "m/s"
        var output = "CAPE: $cape J/kg\nWind Speed 10m: $wind10m $speedUnit\nWind Speed 80m: $wind80m $speedUnit\nWind Speed 100m: $wind100m $speedUnit\n"
        if (wind10m != "N/A" && wind100m != "N/A") {
            try {
                val shear = wind100m.toFloat() - wind10m.toFloat()
                output += "Wind Shear (100m-10m): $shear $speedUnit\n"
            } catch (e: Exception) {
                output += "Wind Shear: N/A\n"
            }
        }
        // Forecasts for next 3 days
        val daily = json.optJSONObject("daily") ?: JSONObject()
        val dates = daily.optJSONArray("time") ?: return output
        val tempmax = daily.optJSONArray("temperature_2m_max") ?: return output
        val tempmin = daily.optJSONArray("temperature_2m_min") ?: return output
        output += "\n--- 3-Day Forecast ---\n"
        for (i in 0 until minOf(3, dates.length())) {
            output += "${dates.getString(i)}: Max: ${tempmax.getString(i)}° ${if (units == "Imperial") "F" else "C"}, Min: ${tempmin.getString(i)}° ${if (units == "Imperial") "F" else "C"}\n"
        }
        return output
    }

    private suspend fun getTomorrowWeatherCodeAndIcon(lat: Double, lon: Double): TomorrowResult? {
        val url = "https://api.tomorrow.io/v4/timelines?location=${lat},${lon}&fields=weatherCodeFullDay&timesteps=1d&units=metric&apikey=${tomorrowApiKey}"
        val client = OkHttpClient()
        val request = Request.Builder().url(url).build()
        val response = client.newCall(request).execute()
        val body = response.body?.string() ?: return null
        val json = JSONObject(body)
        val intervals = json.optJSONObject("data")?.optJSONArray("timelines")?.optJSONObject(0)?.optJSONArray("intervals")
        if (intervals != null && intervals.length() > 0) {
            val code = intervals.getJSONObject(0).optJSONObject("values")?.optInt("weatherCodeFullDay")
            val desc = tomorrowWeatherDesc(code)
            val iconUrl = getTomorrowIconUrl(code)
            return TomorrowResult(code, desc, iconUrl)
        }
        return null
    }

    private fun tomorrowWeatherDesc(code: Int?): String {
        return when (code) {
            1000 -> "Clear"
            1100 -> "Mostly Clear"
            1101 -> "Partly Cloudy"
            1102 -> "Mostly Cloudy"
            1001 -> "Cloudy"
            2000 -> "Fog"
            2100 -> "Light Fog"
            4000 -> "Drizzle"
            4001 -> "Rain"
            4200 -> "Light Rain"
            4201 -> "Heavy Rain"
            5000 -> "Snow"
            5001 -> "Flurries"
            5100 -> "Light Snow"
            5101 -> "Heavy Snow"
            6000 -> "Freezing Drizzle"
            6001 -> "Freezing Rain"
            6200 -> "Light Freezing Rain"
            6201 -> "Heavy Freezing Rain"
            7000 -> "Ice Pellets"
            7101 -> "Heavy Ice Pellets"
            7102 -> "Light Ice Pellets"
            8000 -> "Thunderstorm"
            else -> "Unknown ($code)"
        }
    }

    private fun getTomorrowIconUrl(code: Int?): String? {
        return if (code != null) {
            "https://raw.githubusercontent.com/Tomorrow-IO-API/tomorrow-weather-codes/master/V2_icons/small/png/${code}_clear_small.png"
        } else null
    }

    data class TomorrowResult(val code: Int?, val desc: String, val iconUrl: String?)

    private fun getYandexMapUrl(lat: Double, lon: Double, zoom: Int): String {
        return "https://static-maps.yandex.ru/1.x/?ll=$lon,$lat&size=450,450&z=$zoom&l=map&pt=$lon,$lat,pm2rdm&lang=en_US"
    }

    private fun getTomorrowOverlayUrl(lat: Double, lon: Double, zoom: Int, layer: String): String? {
        val tomorrowLayers = mapOf(
            "Precipitation Intensity" to "precipitationIntensity",
            "Temperature" to "temperature",
            "Wind Speed" to "windSpeed",
            "Cloud Cover" to "cloudCover",
            "Pressure" to "pressure",
            "Wind Direction" to "windDirection",
            "Visibility" to "visibility",
            "Thunderstorm Probability" to "thunderstormProbability",
            "Dew Point" to "dewPoint",
            "Humidity" to "humidity"
        )
        val layerCode = tomorrowLayers[layer] ?: return null
        // Convert lat/lon to tile coordinates
        val (xTile, yTile) = latlonToTile(lat, lon, zoom)
        return "https://api.tomorrow.io/v4/map/tile/$zoom/$xTile/$yTile/$layerCode/now.png?apikey=$tomorrowApiKey"
    }

    private fun latlonToTile(lat: Double, lon: Double, zoom: Int): Pair<Int, Int> {
        val latRad = Math.toRadians(lat)
        val n = Math.pow(2.0, zoom.toDouble())
        val xTile = ((lon + 180.0) / 360.0 * n).toInt()
        val yTile = ((1.0 - Math.log(Math.tan(latRad) + (1 / Math.cos(latRad))) / Math.PI) / 2.0 * n).toInt()
        return Pair(xTile, yTile)
    }

    data class WeatherResult(val current: String, val forecast: String, val alerts: String)
}