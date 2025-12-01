import requests
import re
import base64

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

    def format_forecast(self):
        """Parse and format space weather forecast deterministically"""
        text = self.pull_data()
        if text.startswith("error"):
            return f"❌ {text}"

        output = []

        # Parse Solar Activity
        solar_flux_match = re.search(r'Solar flux\s+(\d+)\s+to\s+(\d+)', text, re.IGNORECASE)
        if solar_flux_match:
            flux_low, flux_high = solar_flux_match.groups()
            output.append(f"☀️ **Solar Flux**: {flux_low}-{flux_high} sfu")

        # Parse Geomagnetic Activity
        geomag_section = re.search(r'Geomagnetic Activity.*?(?=No space|\Z)', text, re.DOTALL | re.IGNORECASE)
        if geomag_section:
            geomag_text = geomag_section.group()
            # Look for activity levels
            if 'quiet' in geomag_text.lower():
                output.append(f"🟢 **Geomagnetic**: Quiet")
            elif 'unsettled' in geomag_text.lower():
                output.append(f"🟡 **Geomagnetic**: Unsettled")
            elif 'active' in geomag_text.lower():
                output.append(f"🟠 **Geomagnetic**: Active")
            elif 'storm' in geomag_text.lower():
                output.append(f"🔴 **Geomagnetic**: Storm conditions")
            else:
                output.append(f"⚪ **Geomagnetic**: Normal")

        # Parse Solar Radiation
        radiation_match = re.search(r'Solar Radiation.*?(\w+)', text, re.IGNORECASE)
        if radiation_match and 'none' not in radiation_match.group().lower():
            output.append(f"☢️ **Solar Radiation**: Elevated")

        # Parse Radio Blackouts
        radio_match = re.search(r'Radio Blackout.*?(\w+)', text, re.IGNORECASE)
        if radio_match and 'none' not in radio_match.group().lower():
            output.append(f"📡 **Radio Blackout**: Possible")

        # Look for notable events in the summary
        if 'flare' in text.lower():
            output.append(f"⚡ **Notable**: Solar flare activity detected")
        if 'cme' in text.lower() or 'coronal mass ejection' in text.lower():
            output.append(f"💥 **Notable**: CME detected")

        return "\n".join(output) if output else "⚪ All quiet - no significant space weather activity"

if __name__=="__main__":
    rr = SpaceWeather()
    print(rr.pull_data())
