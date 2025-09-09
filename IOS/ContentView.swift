
import GoogleMobileAds
import SwiftUI
import CoreLocation

struct ContentView: View {
    @StateObject private var locationManager = LocationManager()
    @State private var useCurrentLoc: Bool = false
    @State private var city: String = ""
    @State private var units: String = "Metric"
    @State private var weatherData: String = ""
    @State private var forecastData: String = ""
    @State private var alertsData: String = ""
    @State private var omData: String = ""
    @State private var mapUrl: String = ""
    @State private var tomorrowIconUrl: String = ""
    @State private var tomorrowDesc: String = ""
    @State private var isLoading: Bool = false

    // App Group for widget data sharing
    let appGroupId = "group.com.example.weatherapp"

    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                ScrollView {
                    VStack(spacing: 16) {
                        HStack {
                            TextField("Enter city name", text: $city)
                                .textFieldStyle(RoundedBorderTextFieldStyle())
                            Button("Use Current Location") {
                                useCurrentLocation()
                            }
                        }
                        .padding(.horizontal)
    func useCurrentLocation() {
        locationManager.requestLocation()
        useCurrentLoc = true
    }
                        Picker("Units", selection: $units) {
                            Text("Metric").tag("Metric")
                            Text("Imperial").tag("Imperial")
                        }
                        .pickerStyle(SegmentedPickerStyle())
                        .padding(.horizontal)
                        Button("Get Weather") {
                            fetchWeather()
                        }
                        .padding()
                        if isLoading {
                            ProgressView()
                        }
                        if !weatherData.isEmpty {
                            CardView(title: "Current Weather", content: weatherData)
                            // Share weather data with widget
                            updateWidgetWeather()
                            if !omData.isEmpty {
                                CardView(title: "Open-Meteo", content: omData)
                            }
                            if !tomorrowIconUrl.isEmpty {
                                HStack {
                                    AsyncImage(url: URL(string: tomorrowIconUrl)) { image in
                                        image.resizable().frame(width: 48, height: 48)
                                    } placeholder: {
                                        ProgressView()
                                    }
                                    Text(tomorrowDesc)
                                        .font(.headline)
                                }
                            }
                            CardView(title: "Forecast", content: forecastData)
                            CardView(title: "Weather Alerts", content: alertsData)
                            if !mapUrl.isEmpty {
                                CardView(title: "Weather Map", content: "")
                                AsyncImage(url: URL(string: mapUrl)) { image in
                                    image.resizable().aspectRatio(contentMode: .fit)
                                } placeholder: {
                                    ProgressView()
                                }
                            }
                        }
    // Function to update widget weather data
    func updateWidgetWeather() {
        let userDefaults = UserDefaults(suiteName: appGroupId)
        // Example: parse temperature and condition from weatherData string
        // You should adapt this to your actual data structure
        let temp = parseTemperature(from: weatherData)
        let cond = parseCondition(from: weatherData)
        userDefaults?.setValue(temp, forKey: "widget_temperature")
        userDefaults?.setValue(cond, forKey: "widget_condition")
        userDefaults?.synchronize()
        // Ask widget to reload
        #if canImport(WidgetKit)
        import WidgetKit
        WidgetCenter.shared.reloadAllTimelines()
        #endif
    }

    func parseTemperature(from data: String) -> String {
        // Simple example: extract first number
        let regex = try? NSRegularExpression(pattern: "(-?\\d+\\.?\\d*)")
        if let match = regex?.firstMatch(in: data, options: [], range: NSRange(location: 0, length: data.utf16.count)),
           let range = Range(match.range(at: 1), in: data) {
            return String(data[range]) + "°C"
        }
        return "--°C"
    }

    func parseCondition(from data: String) -> String {
        // Simple example: extract first word
        let words = data.split(separator: " ")
        return words.first.map { String($0) } ?? "Unknown"
    }
                        // Visual Crossing attribution as clickable link
                        Link("Weather Data Provided by Visual Crossing", destination: URL(string: "https://www.visualcrossing.com/")!)
                            .font(.footnote)
                            .foregroundColor(Color.blue)
                            .padding(.top, 8)
                    }
                }
                // AdMob Banner Ad (unobtrusive, at bottom)
                BannerAdView(adUnitID: "ca-app-pub-xxxxxxxxxxxxxxxx/xxxxxxxxxx")
                    .frame(height: 50)
            }
            .navigationTitle("Weather App")
        }
    }
// AdMob BannerAdView implementation
            struct BannerAdView: UIViewRepresentable {
                let adUnitID: String
            
                func makeUIView(context: Context) -> GADBannerView {
                    let banner = GADBannerView(adSize: kGADAdSizeBanner)
                    banner.adUnitID = adUnitID
                    banner.rootViewController = UIApplication.shared.windows.first?.rootViewController
                    banner.load(GADRequest())
                    return banner
                }
            
                func updateUIView(_ uiView: GADBannerView, context: Context) {}
            }

            struct ContentView: View {
                @State private var city: String = ""
                @State private var units: String = "Metric"
                @State private var weatherData: String = ""
                @State private var forecastData: String = ""
                @State private var alertsData: String = ""
                @State private var omData: String = ""
                @State private var mapUrl: String = ""
                @State private var tomorrowIconUrl: String = ""
                @State private var tomorrowDesc: String = ""
                @State private var isLoading: Bool = false
                @State private var errorMsg: String = ""

                let visualCrossingApiKey = "GD85JQAPJ8T44X8VKURGLFFD9"
                let tomorrowApiKey = "ku1mDhkjQlc8CRZkOzXr8wZ0BjTEUInB"

                var body: some View {
                    NavigationView {
                        ScrollView {
                            VStack(spacing: 16) {
                                TextField("Enter city name", text: $city)
                                    .textFieldStyle(RoundedBorderTextFieldStyle())
                                    .padding(.horizontal)
                                Picker("Units", selection: $units) {
                                    Text("Metric").tag("Metric")
                                    Text("Imperial").tag("Imperial")
                                }
                                .pickerStyle(SegmentedPickerStyle())
                                .padding(.horizontal)
                                Button("Get Weather") {
                                    Task { await fetchWeather() }
                                }
                                .padding()
                                if isLoading {
                                    ProgressView()
                                }
                                if !errorMsg.isEmpty {
                                    Text(errorMsg).foregroundColor(.red).padding()
                                }
                                if !weatherData.isEmpty {
                                    CardView(title: "Current Weather", content: weatherData)
                                    if !omData.isEmpty {
                                        CardView(title: "Open-Meteo", content: omData)
                                    }
                                    if !tomorrowIconUrl.isEmpty {
                                        HStack {
                                            AsyncImage(url: URL(string: tomorrowIconUrl)) { image in
                                                image.resizable().frame(width: 48, height: 48)
                                            } placeholder: {
                                                ProgressView()
                                            }
                                            Text(tomorrowDesc)
                                                .font(.headline)
                                        }
                                    }
                                    CardView(title: "Forecast", content: forecastData)
                                    CardView(title: "Weather Alerts", content: alertsData)
                                    if !mapUrl.isEmpty {
                                        CardView(title: "Weather Map", content: "")
                                        AsyncImage(url: URL(string: mapUrl)) { image in
                                            image.resizable().aspectRatio(contentMode: .fit)
                                        } placeholder: {
                                            ProgressView()
                                        }
                                    }
                                }
                            }
                        }
                        .navigationTitle("Weather App")
                    }
                }

                func fetchWeather() async {
                    isLoading = true
                    errorMsg = ""
                    weatherData = ""
                    forecastData = ""
                    alertsData = ""
                    omData = ""
                    mapUrl = ""
                    tomorrowIconUrl = ""
                    tomorrowDesc = ""
                    var lat: Double?
                    var lon: Double?
                    if useCurrentLoc, let loc = locationManager.location {
                        lat = loc.latitude
                        lon = loc.longitude
                    } else {
                        guard !city.isEmpty else {
                            errorMsg = "Please enter a city name."
                            isLoading = false
                            return
                        }
                        do {
                            (lat, lon) = try await getCoordinates(city: city)
                        } catch {
                            errorMsg = error.localizedDescription
                            isLoading = false
                            return
                        }
                    }
                    do {
                        let (vcCurrent, vcForecast, vcAlerts) = try await getWeatherVisualCrossing(city: city, units: units)
                        let om = try await getWeatherOpenMeteo(lat: lat!, lon: lon!, units: units)
                        let tomorrowCode = try await getTomorrowWeatherCode(lat: lat!, lon: lon!)
                        let tomorrowDescStr = tomorrowWeatherDesc(code: tomorrowCode)
                        let tomorrowIcon = getTomorrowIconUrl(code: tomorrowCode)
                        let map = getYandexMapUrl(lat: lat!, lon: lon!)
                        weatherData = vcCurrent
                        forecastData = vcForecast
                        alertsData = vcAlerts
                        omData = om
                        tomorrowDesc = tomorrowDescStr
                        tomorrowIconUrl = tomorrowIcon ?? ""
                        mapUrl = map
                    } catch {
                        errorMsg = error.localizedDescription
                    }
                    isLoading = false
                }
// LocationManager for CoreLocation
class LocationManager: NSObject, ObservableObject, CLLocationManagerDelegate {
    private let manager = CLLocationManager()
    @Published var location: CLLocationCoordinate2D?

    override init() {
        super.init()
        manager.delegate = self
    }

    func requestLocation() {
        manager.requestWhenInUseAuthorization()
        manager.requestLocation()
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        location = locations.first?.coordinate
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        print("Location error: \(error)")
    }
}

                func getCoordinates(city: String) async throws -> (Double, Double) {
                    let urlStr = "https://geocoding-api.open-meteo.com/v1/search?name=\(city.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? city)&count=1"
                    guard let url = URL(string: urlStr) else { throw URLError(.badURL) }
                    let (data, _) = try await URLSession.shared.data(from: url)
                    if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                        let results = json["results"] as? [[String: Any]],
                        let first = results.first,
                        let lat = first["latitude"] as? Double,
                        let lon = first["longitude"] as? Double {
                        return (lat, lon)
                    }
                    throw NSError(domain: "No coordinates found", code: 0)
                }

                func getWeatherVisualCrossing(city: String, units: String) async throws -> (String, String, String) {
                    let unitGroup = units == "Imperial" ? "us" : "metric"
                    let urlStr = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/\(city.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? city)?unitGroup=\(unitGroup)&key=\(visualCrossingApiKey)&include=current,days,alerts,hours"
                    guard let url = URL(string: urlStr) else { throw URLError(.badURL) }
                    let (data, _) = try await URLSession.shared.data(from: url)
                    guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { throw NSError(domain: "API error", code: 0) }
                    let current = json["currentConditions"] as? [String: Any] ?? [:]
                    let tempUnit = units == "Imperial" ? "°F" : "°C"
                    let speedUnit = units == "Imperial" ? "mph" : "km/h"
                    let precipUnit = units == "Imperial" ? "in" : "mm"
                    let pressureUnit = units == "Imperial" ? "inHg" : "hPa"
                    let visUnit = units == "Imperial" ? "mi" : "km"
                    let now = DateFormatter.localizedString(from: Date(), dateStyle: .medium, timeStyle: .medium)
                    var outputCurrent = "Current Date & Time: \(now)\nWeather in \(city): \(current["conditions"] as? String ?? "N/A")\nTemperature: \(current["temp"] ?? "N/A")\(tempUnit) (Feels like: \(current["feelslike"] ?? "N/A")\(tempUnit))\nHumidity: \(current["humidity"] ?? "N/A")%\nWind Speed: \(current["windspeed"] ?? "N/A") \(speedUnit)\nPrecipitation: \(current["precip"] ?? "N/A") \(precipUnit)\nPressure: \(current["pressure"] ?? "N/A") \(pressureUnit)\nUV Index: \(current["uvindex"] ?? "N/A")\nVisibility: \(current["visibility"] ?? "N/A") \(visUnit)\nSunrise: \(current["sunrise"] ?? "N/A")\nSunset: \(current["sunset"] ?? "N/A")"
                    var outputForecast = "Forecast:\n"
                    let days = json["days"] as? [[String: Any]] ?? []
                    outputForecast += "3-Day Forecast:\n"
                    for i in 0..<min(3, days.count) {
                        let day = days[i]
                        let date = day["datetime"] as? String ?? "N/A"
                        let desc = day["description"] as? String ?? "N/A"
                        let tempmax = day["tempmax"] ?? "N/A"
                        let tempmin = day["tempmin"] ?? "N/A"
                        outputForecast += "\(date): \(desc)\n  Max: \(tempmax)\(tempUnit), Min: \(tempmin)\(tempUnit)\n"
                    }
                    var outputAlerts = ""
                    let alerts = json["alerts"] as? [[String: Any]] ?? []
                    if !alerts.isEmpty {
                        outputAlerts += "Weather Alerts:\n"
                        for alert in alerts {
                            let title = alert["event"] as? String ?? "Alert"
                            let desc = alert["description"] as? String ?? ""
                            let starts = alert["onset"] as? String ?? "N/A"
                            let ends = alert["ends"] as? String ?? "N/A"
                            outputAlerts += "\(title):\n  Starts: \(starts)\n  Ends: \(ends)\n  \(desc)\n"
                        }
                    } else {
                        outputAlerts += "No active weather alerts.\n"
                    }
                    return (outputCurrent, outputForecast, outputAlerts)
                }

                func getWeatherOpenMeteo(lat: Double, lon: Double, units: String) async throws -> String {
                    let urlStr = "https://api.open-meteo.com/v1/forecast?latitude=\(lat)&longitude=\(lon)&current_weather=true&hourly=cape,wind_speed_10m,wind_speed_80m,wind_speed_100m&daily=temperature_2m_max,temperature_2m_min,weathercode&timezone=auto"
                    guard let url = URL(string: urlStr) else { throw URLError(.badURL) }
                    let (data, _) = try await URLSession.shared.data(from: url)
                    guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { throw NSError(domain: "API error", code: 0) }
                    let hourly = json["hourly"] as? [String: Any] ?? [:]
                    let cape = (hourly["cape"] as? [Any])?.first as? Double ?? 0.0
                    let wind10m = (hourly["wind_speed_10m"] as? [Any])?.first as? Double ?? 0.0
                    let wind80m = (hourly["wind_speed_80m"] as? [Any])?.first as? Double ?? 0.0
                    let wind100m = (hourly["wind_speed_100m"] as? [Any])?.first as? Double ?? 0.0
                    let speedUnit = units == "Imperial" ? "mph" : "m/s"
                    var output = "CAPE: \(cape) J/kg\nWind Speed 10m: \(wind10m) \(speedUnit)\nWind Speed 80m: \(wind80m) \(speedUnit)\nWind Speed 100m: \(wind100m) \(speedUnit)\n"
                    if wind10m != 0.0 && wind100m != 0.0 {
                        let shear = wind100m - wind10m
                        output += "Wind Shear (100m-10m): \(shear) \(speedUnit)\n"
                    }
                    let daily = json["daily"] as? [String: Any] ?? [:]
                    let dates = daily["time"] as? [String] ?? []
                    let tempmax = daily["temperature_2m_max"] as? [Double] ?? []
                    let tempmin = daily["temperature_2m_min"] as? [Double] ?? []
                    output += "\n--- 3-Day Forecast ---\n"
                    for i in 0..<min(3, dates.count) {
                        output += "\(dates[i]): Max: \(tempmax[i])° \(units == "Imperial" ? "F" : "C"), Min: \(tempmin[i])° \(units == "Imperial" ? "F" : "C")\n"
                    }
                    return output
                }

                func getTomorrowWeatherCode(lat: Double, lon: Double) async throws -> Int? {
                    let urlStr = "https://api.tomorrow.io/v4/timelines?location=\(lat),\(lon)&fields=weatherCodeFullDay&timesteps=1d&units=metric&apikey=\(tomorrowApiKey)"
                    guard let url = URL(string: urlStr) else { throw URLError(.badURL) }
                    let (data, _) = try await URLSession.shared.data(from: url)
                    guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                        let dataObj = json["data"] as? [String: Any],
                        let timelines = dataObj["timelines"] as? [[String: Any]],
                        let intervals = timelines.first?["intervals"] as? [[String: Any]],
                        let values = intervals.first?["values"] as? [String: Any],
                        let code = values["weatherCodeFullDay"] as? Int else { return nil }
                    return code
                }

                func tomorrowWeatherDesc(code: Int?) -> String {
                    switch code {
                    case 1000: return "Clear"
                    case 1100: return "Mostly Clear"
                    case 1101: return "Partly Cloudy"
                    case 1102: return "Mostly Cloudy"
                    case 1001: return "Cloudy"
                    case 2000: return "Fog"
                    case 2100: return "Light Fog"
                    case 4000: return "Drizzle"
                    case 4001: return "Rain"
                    case 4200: return "Light Rain"
                    case 4201: return "Heavy Rain"
                    case 5000: return "Snow"
                    case 5001: return "Flurries"
                    case 5100: return "Light Snow"
                    case 5101: return "Heavy Snow"
                    case 6000: return "Freezing Drizzle"
                    case 6001: return "Freezing Rain"
                    case 6200: return "Light Freezing Rain"
                    case 6201: return "Heavy Freezing Rain"
                    case 7000: return "Ice Pellets"
                    case 7101: return "Heavy Ice Pellets"
                    case 7102: return "Light Ice Pellets"
                    case 8000: return "Thunderstorm"
                    case .none: return "Unknown"
                    default: return "Unknown (\(code ?? -1))"
                    }
                }

                func getTomorrowIconUrl(code: Int?) -> String? {
                    if let code = code {
                        return "https://raw.githubusercontent.com/Tomorrow-IO-API/tomorrow-weather-codes/master/V2_icons/small/png/\(code)_clear_small.png"
                    }
                    return nil
                }

                func getYandexMapUrl(lat: Double, lon: Double) -> String {
                    return "https://static-maps.yandex.ru/1.x/?ll=\(lon),\(lat)&size=450,450&z=10&l=map&pt=\(lon),\(lat),pm2rdm&lang=en_US"
                }
            }

            struct CardView: View {
                let title: String
                let content: String
                var body: some View {
                    VStack(alignment: .leading, spacing: 8) {
                        Text(title).font(.title2).bold()
                        if !content.isEmpty {
                            Text(content).font(.body).lineLimit(nil)
                        }
                    }
                    .padding()
                    .background(Color(.secondarySystemBackground))
                    .cornerRadius(12)
                    .shadow(radius: 2)
                    .padding(.horizontal)
                }
            }
        }
    }
}

