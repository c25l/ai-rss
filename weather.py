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

    def _get_weather_icon_color(self, description):
        """Get color based on weather condition"""
        description = description.lower()
        if 'sunny' in description or 'clear' in description:
            return '#FFD700'
        elif 'rain' in description or 'shower' in description:
            return '#4682B4'
        elif 'snow' in description:
            return '#E0FFFF'
        elif 'storm' in description or 'thunder' in description:
            return '#9932CC'
        elif 'cloudy' in description:
            return '#A9A9A9'
        else:
            return '#87CEEB'

    def pull_data(self):
        url="https://forecast.weather.gov/MapClick.php?lat=40.165729&lon=-105.101194"
        resp = requests.get(url)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            forecast = soup.find(id="detailed-forecast")
            return str(forecast)
        return "failed"

    def get_alerts(self, lat=40.165729, lon=-105.101194):
        """Fetch active NWS alerts for the location"""
        try:
            headers = {
                'User-Agent': '(Weather Script, contact@example.com)'
            }
            url = f"https://api.weather.gov/alerts/active?point={lat},{lon}"
            resp = requests.get(url, headers=headers, timeout=10)

            if resp.status_code == 200:
                data = resp.json()
                features = data.get('features', [])

                alerts = []
                for feature in features:
                    props = feature.get('properties', {})
                    event = props.get('event', 'Unknown Alert')
                    headline = props.get('headline', '')
                    severity = props.get('severity', '')

                    if severity == 'Extreme':
                        emoji = '🚨'
                    elif severity == 'Severe':
                        emoji = '⚠️'
                    elif severity == 'Moderate':
                        emoji = '⚡'
                    else:
                        emoji = 'ℹ️'

                    alerts.append(f"{emoji} **{event}**: {headline}")

                return alerts
            return []
        except Exception as e:
            print(f"Error fetching NWS alerts: {e}")
            return []

    def _parse_forecast_data(self, max_periods=8):
        """Parse forecast data and return structured data"""
        html = self.pull_data()
        if html == "failed":
            return None

        soup = BeautifulSoup(html, "html.parser")
        periods = soup.find_all("div", class_="row-forecast")

        if not periods:
            return None

        forecast_data = []
        for period in periods[:max_periods]:
            label = period.find("div", class_="forecast-label")
            text = period.find("div", class_="forecast-text")

            if label and text:
                name = label.get_text(strip=True)
                desc = text.get_text(strip=True)
                condition = desc.split('.')[0].strip()

                # Extract temperature
                temp_match = re.search(r'\b(?:high|low)\s+(?:near\s+)?(\d+)', desc, re.IGNORECASE)
                temp = int(temp_match.group(1)) if temp_match else None

                # Determine if high or low
                is_high = 'high' in desc.lower()[:50]

                forecast_data.append({
                    'name': name,
                    'temp': temp,
                    'is_high': is_high,
                    'condition': condition,
                    'description': desc
                })

        return forecast_data

    def generate_temperature_svg(self, width=400, height=120):
        """Generate SVG temperature graph for forecast"""
        forecast_data = self._parse_forecast_data(max_periods=8)
        if not forecast_data:
            return ""

        # Filter periods with temperatures
        temps_data = [(d['name'][:8], d['temp'], d['is_high'], d['condition']) 
                      for d in forecast_data if d['temp'] is not None]

        if len(temps_data) < 2:
            return ""

        # Chart dimensions
        margin_left = 35
        margin_right = 15
        margin_top = 25
        margin_bottom = 35
        chart_width = width - margin_left - margin_right
        chart_height = height - margin_top - margin_bottom

        # Get temp range
        temps = [t[1] for t in temps_data]
        min_temp = min(temps) - 5
        max_temp = max(temps) + 5
        temp_range = max_temp - min_temp

        svg_parts = []
        svg_parts.append(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" style="background-color: #1a1a2e;">''')

        # Title
        svg_parts.append(f'''  <text x="{width/2}" y="15" text-anchor="middle" fill="#CCCCCC" font-size="11" font-family="Arial">Temperature Forecast</text>''')

        # Y-axis labels
        for i in range(5):
            temp_val = min_temp + (temp_range * i / 4)
            y = margin_top + chart_height - (chart_height * i / 4)
            svg_parts.append(f'''  <text x="{margin_left - 5}" y="{y + 3}" text-anchor="end" fill="#888" font-size="9" font-family="Arial">{temp_val:.0f}°</text>''')
            svg_parts.append(f'''  <line x1="{margin_left}" y1="{y}" x2="{width - margin_right}" y2="{y}" stroke="#333" stroke-width="0.5" stroke-dasharray="3,3"/>''')

        # Plot points and lines
        points = []
        x_step = chart_width / (len(temps_data) - 1) if len(temps_data) > 1 else chart_width

        for i, (name, temp, is_high, condition) in enumerate(temps_data):
            x = margin_left + i * x_step
            y = margin_top + chart_height - ((temp - min_temp) / temp_range * chart_height)
            points.append((x, y, temp, is_high, name, condition))

        # Draw line connecting points
        if len(points) > 1:
            path_d = f"M {points[0][0]} {points[0][1]}"
            for x, y, _, _, _, _ in points[1:]:
                path_d += f" L {x} {y}"
            svg_parts.append(f'''  <path d="{path_d}" fill="none" stroke="#4FC3F7" stroke-width="2" opacity="0.8"/>''')

        # Draw points and labels
        for x, y, temp, is_high, name, condition in points:
            color = '#FF6B6B' if is_high else '#4FC3F7'
            svg_parts.append(f'''  <circle cx="{x}" cy="{y}" r="4" fill="{color}"/>''')
            svg_parts.append(f'''  <text x="{x}" y="{y - 8}" text-anchor="middle" fill="{color}" font-size="9" font-family="Arial" font-weight="bold">{temp}°</text>''')
            # X-axis label (period name)
            svg_parts.append(f'''  <text x="{x}" y="{height - 8}" text-anchor="middle" fill="#888" font-size="7" font-family="Arial">{name}</text>''')

        # Legend
        svg_parts.append(f'''  <circle cx="{width - 60}" cy="{margin_top + 5}" r="3" fill="#FF6B6B"/>''')
        svg_parts.append(f'''  <text x="{width - 53}" y="{margin_top + 8}" fill="#888" font-size="7" font-family="Arial">High</text>''')
        svg_parts.append(f'''  <circle cx="{width - 30}" cy="{margin_top + 5}" r="3" fill="#4FC3F7"/>''')
        svg_parts.append(f'''  <text x="{width - 23}" y="{margin_top + 8}" fill="#888" font-size="7" font-family="Arial">Low</text>''')

        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)

    def format_forecast(self, max_periods=6, include_graph=True):
        """Parse and format weather forecast deterministically"""
        html = self.pull_data()
        if html == "failed":
            return "❌ Unable to fetch weather data"

        soup = BeautifulSoup(html, "html.parser")
        periods = soup.find_all("div", class_="row-forecast")

        if not periods:
            return "❌ No forecast data available"

        output = []

        # Add alerts at the top if any exist
        alerts = self.get_alerts()
        if alerts:
            output.append("### 🚨 Active Alerts")
            for alert in alerts:
                output.append(f"- {alert}")
            output.append("")

        # Add temperature graph if requested
        if include_graph:
            graph_svg = self.generate_temperature_svg()
            if graph_svg:
                output.append('<div style="text-align: center;">')
                output.append(graph_svg)
                output.append('</div>')
                output.append("")

        for i, period in enumerate(periods[:max_periods]):
            label = period.find("div", class_="forecast-label")
            text = period.find("div", class_="forecast-text")

            if label and text:
                name = label.get_text(strip=True)
                desc = text.get_text(strip=True)
                condition = desc.split('.')[0].strip()
                temp_match = re.search(r'\b(high|low)\s+(?:near\s+)?(\d+)', desc, re.IGNORECASE)
                temp_text = f"{temp_match.group(2)}°F" if temp_match else ""

                emoji = self._get_weather_emoji(desc)
                if temp_text:
                    output.append(f"- {emoji} **{name}**: {temp_text} - {condition}")
                else:
                    output.append(f"- {emoji} **{name}**: {condition}")

        return "\n".join(output) if output else "❌ No forecast periods found"
           

if __name__=="__main__":
    rr = Weather()
    print(rr.format_forecast())
