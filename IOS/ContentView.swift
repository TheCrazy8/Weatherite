import SwiftUI

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
                        fetchWeather()
                    }
                    .padding()
                    if isLoading {
                        ProgressView()
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

    func fetchWeather() {
        isLoading = true
        weatherData = ""
        forecastData = ""
        alertsData = ""
        omData = ""
        mapUrl = ""
        tomorrowIconUrl = ""
        tomorrowDesc = ""
        // Call your APIs here using URLSession and update state variables
        // See Python logic for API endpoints and parsing
        // For brevity, actual networking code is omitted
        // You can use async/await with URLSession for clean code
        // Example: fetch coordinates, then weather, then update UI
        isLoading = false
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
