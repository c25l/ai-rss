import requests
import json
class Weather(object):
    def __init__(self):
        pass
    
    def _get_weather_icon(self, condition):
        """Convert weather condition to Unicode icon"""
        condition = condition.lower()
        if 'sunny' in condition or 'clear' in condition:
            return '☀️'
        elif 'partly cloudy' in condition or 'partly sunny' in condition:
            return '⛅'
        elif 'cloudy' in condition or 'overcast' in condition:
            return '☁️'
        elif 'rain' in condition or 'shower' in condition:
            return '🌧️'
        elif 'storm' in condition or 'thunder' in condition:
            return '⛈️'
        elif 'snow' in condition:
            return '❄️'
        elif 'fog' in condition or 'mist' in condition:
            return '🌫️'
        else:
            return '🌤️'
    
    def _create_sparkline(self, values, width=100, height=20):
        """Create SVG sparkline from temperature values"""
        if not values:
            return ""
        
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val if max_val != min_val else 1
        
        points = []
        for i, val in enumerate(values):
            x = (i / (len(values) - 1)) * width if len(values) > 1 else width/2
            y = height - ((val - min_val) / range_val) * height
            points.append(f"{x:.1f},{y:.1f}")
        
        return f"""<svg width="{width}" height="{height}" style="display:inline-block;vertical-align:middle;">
<polyline fill="none" stroke="#2563eb" stroke-width="2" points="{' '.join(points)}"/>
<text x="2" y="12" font-size="10" fill="#666">{min_val}°</text>
<text x="{width-20}" y="12" font-size="10" fill="#666">{max_val}°</text>
</svg>"""
    
    def pull_data(self):
        url="https://api.weather.gov/gridpoints/BOU/60,81/forecast"
        resp = requests.get(url)
        if resp.status_code == 200:
            data = json.loads(resp.text)
            periods = data.get("properties", {}).get("periods", [])[:6]

            if not periods:
                return "No weather data available"

            # Group periods by day (combine day/night pairs)
            daily_forecasts = {}
            temps = []

            for period in periods:
                temp = period.get('temperature')
                if temp:
                    temps.append(temp)

                name = period.get('name', '')
                is_day = period.get('isDaytime', True)

                # Extract day name from period name
                day_name = name.replace(' Night', '').replace('This ', '').replace('Tonight', 'Today')

                if day_name not in daily_forecasts:
                    daily_forecasts[day_name] = {'day': None, 'night': None}

                period_data = {
                    'temp': temp,
                    'icon': self._get_weather_icon(period.get('shortForecast', '')),
                    'forecast': period.get('shortForecast', '')
                }

                if is_day:
                    daily_forecasts[day_name]['day'] = period_data
                else:
                    daily_forecasts[day_name]['night'] = period_data

            html_parts = ["<div style='font-family:sans-serif;'>"]

            # Create combined day/night boxes - limit to 3 days
            count = 0
            for day_name, forecast in daily_forecasts.items():
                if count >= 3:
                    break

                day_data = forecast.get('day')
                night_data = forecast.get('night')

                # Use day icon if available, otherwise night icon
                icon = day_data['icon'] if day_data else (night_data['icon'] if night_data else '🌤️')

                # Format temperature range
                temps_for_day = []
                if day_data and day_data['temp']:
                    temps_for_day.append(day_data['temp'])
                if night_data and night_data['temp']:
                    temps_for_day.append(night_data['temp'])

                if temps_for_day:
                    high_temp = max(temps_for_day)
                    low_temp = min(temps_for_day)
                    temp_str = f"{high_temp}°/{low_temp}°F" if high_temp != low_temp else f"{high_temp}°F"
                else:
                    temp_str = "N/A"

                html_parts.append(f"""
<div style='display:inline-block;margin:5px;padding:8px;border:1px solid #ddd;border-radius:4px;text-align:center;min-width:100px;'>
<div style='font-size:32px;'>{icon}</div>
<div style='font-size:16px;font-weight:bold;'>{day_name}</div>
<div style='font-size:18px;color:#333;'>{temp_str}</div>
</div>""")
                count += 1

            html_parts.append("</div>")
            return "".join(html_parts)
        else:
            return "error fetching weather"

if __name__=="__main__":
    rr = Weather()
    print(rr.pull_data())
