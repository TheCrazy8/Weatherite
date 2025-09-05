package com.example.weatherapp

import android.os.Bundle
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import com.bumptech.glide.Glide
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

    private val visualCrossingApiKey = "YOUR_VISUAL_CROSSING_API_KEY"
    private val tomorrowApiKey = "YOUR_TOMORROW_IO_API_KEY"

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
            // 1. Get coordinates
            val (lat, lon) = getCoordinates(city)
            // 2. Get weather data
            val vcWeather = getWeatherVisualCrossing(city, units, forecastType)
            val omWeather = getWeatherOpenMeteo(lat, lon, units)
            val tomorrowCode = getTomorrowWeatherCode(lat, lon)
            // 3. Get map image
            val mapUrl = getYandexMapUrl(lat, lon, zoom)
            // 4. Get overlay image (optional)
            // ...implement overlay fetch if needed...

            withContext(Dispatchers.Main) {
                currentWeather.text = "--- Visual Crossing ---\n${vcWeather.current}\n--- Open-Meteo ---\n${omWeather}"
                forecastWeather.text = vcWeather.forecast
                alertsWeather.text = vcWeather.alerts
                Glide.with(this@MainActivity).load(mapUrl).into(mapImage)
                // Show Tomorrow.io icon/desc if available
                // ...implement icon display...
            }
        }
    }

    private suspend fun getCoordinates(city: String): Pair<Double, Double> {
        // Use OkHttp to fetch coordinates from Open-Meteo
        // ...implement API call...
        return Pair(52.37, 4.89) // Example: Amsterdam
    }

    private suspend fun getWeatherVisualCrossing(city: String, units: String, forecastType: String): WeatherResult {
        // Use OkHttp to fetch weather from Visual Crossing
        // ...implement API call and parse...
        return WeatherResult("Current weather...", "Forecast...", "Alerts...")
    }

    private suspend fun getWeatherOpenMeteo(lat: Double, lon: Double, units: String): String {
        // Use OkHttp to fetch weather from Open-Meteo
        // ...implement API call and parse...
        return "Open-Meteo data..."
    }

    private suspend fun getTomorrowWeatherCode(lat: Double, lon: Double): Int? {
        // Use OkHttp to fetch weatherCodeFullDay from Tomorrow.io
        // ...implement API call and parse...
        return null
    }

    private fun getYandexMapUrl(lat: Double, lon: Double, zoom: Int): String {
        return "https://static-maps.yandex.ru/1.x/?ll=$lon,$lat&size=450,450&z=$zoom&l=map&pt=$lon,$lat,pm2rdm&lang=en_US"
    }

    data class WeatherResult(val current: String, val forecast: String, val alerts: String)
}