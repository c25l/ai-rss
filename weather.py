import requests
import json
from bs4 import BeautifulSoup
import re

class Weather(object):
    def __init__(self):
        pass

    def _get_weather_emoji(self, description):
        """Map weather descriptions to emojis"""
        description = description.lower()
        if 'sunny' in description or 'clear' in description:
            return '☀️'
        elif 'partly cloudy' in description or 'mostly sunny' in description:
            return '⛅'
        elif 'mostly cloudy' in description or 'cloudy' in description:
            return '☁️'
        elif 'rain' in description or 'shower' in description:
            return '🌧️'
        elif 'snow' in description:
            return '❄️'
        elif 'storm' in description or 'thunder' in description:
            return '⛈️'
        elif 'fog' in description:
            return '🌫️'
        elif 'wind' in description:
            return '💨'
        else:
            return '🌤️'

    def pull_data(self):
        url="https://forecast.weather.gov/MapClick.php?lat=40.165729&lon=-105.101194"
        resp = requests.get(url)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            forecast = soup.find(id="detailed-forecast")
            return str(forecast)
        return "failed"

    def format_forecast(self, max_periods=6):
        """Parse and format weather forecast deterministically"""
        html = self.pull_data()
        if html == "failed":
            return "❌ Unable to fetch weather data"

        soup = BeautifulSoup(html, "html.parser")
        periods = soup.find_all("div", class_="row-forecast")

        if not periods:
            return "❌ No forecast data available"

        output = []
        for i, period in enumerate(periods[:max_periods]):
            label = period.find("div", class_="forecast-label")
            text = period.find("div", class_="forecast-text")

            if label and text:
                name = label.get_text(strip=True)
                desc = text.get_text(strip=True)

                # Extract key weather condition (first sentence)
                condition = desc.split('.')[0].strip()

                # Extract temperature if present
                temp_match = re.search(r'\b(high|low)\s+(?:near\s+)?(\d+)', desc, re.IGNORECASE)
                temp_text = f"{temp_match.group(2)}°F" if temp_match else ""

                emoji = self._get_weather_emoji(desc)
                if temp_text:
                    output.append(f"{emoji} **{name}**: {temp_text} - {condition}")
                else:
                    output.append(f"{emoji} **{name}**: {condition}")

        return "<br/>\n".join(output) if output else "❌ No forecast periods found"
           

if __name__=="__main__":
    rr = Weather()
    print(rr.pull_data())
