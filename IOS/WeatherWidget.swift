import WidgetKit
import SwiftUI

struct WeatherEntry: TimelineEntry {
    let date: Date
    let temperature: String
    let condition: String
}

struct WeatherProvider: TimelineProvider {
    func placeholder(in context: Context) -> WeatherEntry {
        WeatherEntry(date: Date(), temperature: "--°C", condition: "Loading...")
    }

    func getSnapshot(in context: Context, completion: @escaping (WeatherEntry) -> ()) {
        let entry = WeatherEntry(date: Date(), temperature: "22°C", condition: "Sunny")
        completion(entry)
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<WeatherEntry>) -> ()) {
        let entry = WeatherEntry(date: Date(), temperature: "22°C", condition: "Sunny")
        let timeline = Timeline(entries: [entry], policy: .atEnd)
        completion(timeline)
    }
}

struct WeatherWidgetEntryView : View {
    var entry: WeatherProvider.Entry

    var body: some View {
        VStack {
            Text(entry.temperature)
                .font(.largeTitle)
                .bold()
            Text(entry.condition)
                .font(.headline)
        }
        .padding()
    }
}

@main
struct WeatherWidget: Widget {
    let kind: String = "WeatherWidget"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: WeatherProvider()) { entry in
            WeatherWidgetEntryView(entry: entry)
        }
        .configurationDisplayName("Weather Widget")
        .description("Shows the current weather.")
        .supportedFamilies([.systemSmall, .systemMedium])
    }
}
