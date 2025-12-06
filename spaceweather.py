import requests
import re
import json
import claude

class SpaceWeather(object):
    def __init__(self):
        pass
    
    def _parse_kp_index(self, text):
        """Extract Kp index values from forecast text"""
        # Look for decimal Kp values in the breakdown table
        kp_matches = re.findall(r'(\d+\.?\d*)\s+(?=\d+\.?\d*\s+\d+\.?\d*\s*$)', text, re.MULTILINE)
        if not kp_matches:
            # Fallback to looking for "Kp X" pattern
            kp_matches = re.findall(r'Kp\s*(\d+\.?\d*)', text)
        return [float(k) for k in kp_matches] if kp_matches else []
    
    def _parse_solar_flux(self, text):
        """Extract solar flux values"""
        flux_matches = re.findall(r'10\.7\s*cm\s*Radio\s*Flux[:\s]*(\d+)', text, re.IGNORECASE)
        return [int(f) for f in flux_matches] if flux_matches else []
    
    def _create_kp_chart(self, kp_values, width=200, height=40):
        """Create SVG chart for Kp index"""
        if not kp_values:
            return ""
        
        bar_width = width / len(kp_values)
        bars = []
        
        for i, kp in enumerate(kp_values):
            x = i * bar_width
            bar_height = (kp / 9) * height  # Kp scale 0-9
            color = self._get_kp_color(int(kp))
            bars.append(f'<rect x="{x}" y="{height-bar_height}" width="{bar_width-2}" height="{bar_height}" fill="{color}"/>')
            bars.append(f'<text x="{x + bar_width/2}" y="{height + 12}" text-anchor="middle" font-size="10">{kp:.1f}</text>')
        
        return f"""<svg width="{width}" height="{height + 15}" style="display:inline-block;">
{chr(10).join(bars)}
<text x="0" y="-5" font-size="10" fill="#666">Kp Index</text>
</svg>"""
    
    def _get_kp_color(self, kp):
        """Get color based on Kp index severity"""
        if kp <= 2:
            return "#22c55e"  # Green - quiet
        elif kp <= 4:
            return "#eab308"  # Yellow - unsettled
        elif kp <= 6:
            return "#f97316"  # Orange - active
        elif kp <= 8:
            return "#ef4444"  # Red - storm
        else:
            return "#7c2d12"  # Dark red - severe
    
    def _get_activity_level(self, kp):
        """Get activity description from Kp index"""
        if kp <= 2:
            return "Quiet"
        elif kp <= 4:
            return "Unsettled"
        elif kp <= 6:
            return "Active"
        elif kp <= 8:
            return "Storm"
        else:
            return "Severe Storm"
    
    def pull_data(self):
        """Fetch raw space weather forecast text"""
        txt_url = "https://services.swpc.noaa.gov/text/3-day-forecast.txt"
        try:
            txt_resp = requests.get(txt_url, timeout=10)
            if txt_resp.status_code != 200:
                return "error fetching space weather"
            return txt_resp.text
        except Exception as e:
            return f"error fetching space weather: {e}"

    def _parse_geomag_activity(self, text):
        """Extract geomagnetic activity levels from forecast"""
        # Look for lines like "Geomagnetic Activity Summary:" followed by date and activity level
        activity_pattern = re.compile(r'(\w{3}\s+\d{2})\s+(\w+(?:\s+to\s+\w+)?)', re.MULTILINE)
        matches = activity_pattern.findall(text)
        return matches[:3]  # Return first 3 days

    def _get_activity_emoji(self, activity):
        """Map activity level to emoji"""
        activity = activity.lower()
        if 'quiet' in activity or 'inactive' in activity:
            return '🟢'
        elif 'unsettled' in activity:
            return '🟡'
        elif 'active' in activity:
            return '🟠'
        elif 'minor' in activity or 'storm' in activity:
            return '🔴'
        elif 'moderate' in activity or 'strong' in activity or 'severe' in activity:
            return '🔴🔴'
        else:
            return '⚪'

    def _fetch_current_data(self):
        """Fetch current space weather data from NOAA APIs"""
        data = {}

        try:
            # X-ray flux (current and recent max)
            xray_resp = requests.get('https://services.swpc.noaa.gov/json/goes/primary/xray-flares-latest.json', timeout=10)
            if xray_resp.status_code == 200:
                xray_data = xray_resp.json()
                if xray_data:
                    latest = xray_data[0]
                    data['xray_current'] = latest.get('current_class', 'N/A')
                    data['xray_max_24h'] = latest.get('max_class', 'N/A')
                    data['xray_max_time'] = latest.get('max_time', 'N/A')
        except:
            pass

        try:
            # Solar flux (10.7cm)
            flux_resp = requests.get('https://services.swpc.noaa.gov/products/summary/10cm-flux.json', timeout=10)
            if flux_resp.status_code == 200:
                flux_data = flux_resp.json()
                data['solar_flux'] = flux_data.get('Flux', 'N/A')
        except:
            pass

        try:
            # Solar wind
            wind_resp = requests.get('https://services.swpc.noaa.gov/products/summary/solar-wind-mag-field.json', timeout=10)
            if wind_resp.status_code == 200:
                wind_data = wind_resp.json()
                data['solar_wind_bt'] = wind_data.get('Bt', 'N/A')
                data['solar_wind_bz'] = wind_data.get('Bz', 'N/A')
        except:
            pass

        return data

    def format_forecast(self):
        """Parse and format space weather forecast with LLM analysis"""
        # Get 3-day forecast text (includes peak Kp)
        forecast_text = self.pull_data()
        if forecast_text.startswith("error"):
            return f"❌ {forecast_text}"

        # Get current data from JSON APIs
        current_data = self._fetch_current_data()

        # Prepare data for Claude
        data_summary = f"""
# Space Weather Data

## 3-Day Forecast (includes 24h peak Kp):
{forecast_text}

## Current Real-Time Values:
- X-ray Class (current): {current_data.get('xray_current', 'N/A')}
- X-ray Class (24h peak): {current_data.get('xray_max_24h', 'N/A')} at {current_data.get('xray_max_time', 'N/A')}
- Solar Flux (10.7cm): {current_data.get('solar_flux', 'N/A')} sfu
- Solar Wind Bt: {current_data.get('solar_wind_bt', 'N/A')} nT
- Solar Wind Bz: {current_data.get('solar_wind_bz', 'N/A')} nT
"""

        # Use Claude to create concise summary
        prompt = """Summarize this space weather data concisely. Format as follows:

For each metric, show: [Emoji] **Metric Name**: Current value (24h peak: X)

Include:
- Kp index (geomagnetic activity)
- X-ray flux class
- Solar flux
- Notable events or alerts

Use <br/> tags for line breaks between each line. Be very concise - max 5 lines total.
Do not include headers or explanations, just the formatted lines.

Data:
""" + data_summary

        result = claude.Claude().generate(prompt)

        # Ensure it ends with proper formatting
        if result and not result.endswith('<br/>'):
            return result.strip()
        return result if result else "⚪ All quiet - no significant space weather activity"

if __name__=="__main__":
    rr = SpaceWeather()
    print(rr.pull_data())
