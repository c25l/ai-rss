import requests
import json
from bs4 import BeautifulSoup

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
        url="https://forecast.weather.gov/MapClick.php?lat=40.165729&lon=-105.101194"
        resp = requests.get(url)
        # url="https://api.weather.gov/gridpoints/BOU/60,81/forecast"
        # resp = requests.get(url)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            forecast = soup.find(id="detailed-forecast")
            return str(forecast)
        return "failed"
           

if __name__=="__main__":
    rr = Weather()
    print(rr.pull_data())
