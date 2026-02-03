import requests
import re
import json

class SpaceWeather(object):
    def __init__(self):
        pass
    
    def _parse_kp_index(self, text):
        """Extract Kp index values from forecast text"""
        kp_matches = re.findall(r'(\d+\.?\d*)\s+(?=\d+\.?\d*\s+\d+\.?\d*\s*$)', text, re.MULTILINE)
        if not kp_matches:
            kp_matches = re.findall(r'Kp\s*(\d+\.?\d*)', text)
        return [float(k) for k in kp_matches] if kp_matches else []
    
    def _parse_solar_flux(self, text):
        """Extract solar flux values"""
        flux_matches = re.findall(r'10\.7\s*cm\s*Radio\s*Flux[:\s]*(\d+)', text, re.IGNORECASE)
        return [int(f) for f in flux_matches] if flux_matches else []

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
        activity_pattern = re.compile(r'(\w{3}\s+\d{2})\s+(\w+(?:\s+to\s+\w+)?)', re.MULTILINE)
        matches = activity_pattern.findall(text)
        return matches[:3]

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
            flux_resp = requests.get('https://services.swpc.noaa.gov/products/summary/10cm-flux.json', timeout=10)
            if flux_resp.status_code == 200:
                flux_data = flux_resp.json()
                data['solar_flux'] = flux_data.get('Flux', 'N/A')
        except:
            pass

        try:
            wind_resp = requests.get('https://services.swpc.noaa.gov/products/summary/solar-wind-mag-field.json', timeout=10)
            if wind_resp.status_code == 200:
                wind_data = wind_resp.json()
                data['solar_wind_bt'] = wind_data.get('Bt', 'N/A')
                data['solar_wind_bz'] = wind_data.get('Bz', 'N/A')
        except:
            pass

        return data

    def _fetch_kp_history(self):
        """Fetch recent Kp index history for charting"""
        try:
            # Get planetary K-index (3-hour intervals)
            kp_resp = requests.get('https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json', timeout=10)
            if kp_resp.status_code == 200:
                kp_data = kp_resp.json()
                # Skip header row (index 0), get last 8 entries (24 hours of 3-hour periods)
                if len(kp_data) > 1:
                    recent = kp_data[-8:]  # Last 8 3-hour periods
                    return [(entry[0], float(entry[1])) for entry in recent if len(entry) > 1]
        except:
            pass
        return []

    def generate_kp_chart_svg(self, width=400, height=100):
        """Generate SVG bar chart for Kp index history"""
        kp_history = self._fetch_kp_history()
        if not kp_history:
            return ""

        margin_left = 30
        margin_right = 10
        margin_top = 25
        margin_bottom = 30
        chart_width = width - margin_left - margin_right
        chart_height = height - margin_top - margin_bottom

        bar_width = chart_width / len(kp_history) - 4
        max_kp = 9  # Kp scale is 0-9

        svg_parts = []
        svg_parts.append(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" style="background-color: #1a1a2e;">''')

        # Title
        svg_parts.append(f'''  <text x="{width/2}" y="15" text-anchor="middle" fill="#CCCCCC" font-size="11" font-family="Arial">Kp Index (24h)</text>''')

        # Y-axis labels and grid
        for kp_val in [0, 3, 5, 7, 9]:
            y = margin_top + chart_height - (kp_val / max_kp * chart_height)
            svg_parts.append(f'''  <text x="{margin_left - 5}" y="{y + 3}" text-anchor="end" fill="#888" font-size="8" font-family="Arial">{kp_val}</text>''')
            svg_parts.append(f'''  <line x1="{margin_left}" y1="{y}" x2="{width - margin_right}" y2="{y}" stroke="#333" stroke-width="0.5" stroke-dasharray="3,3"/>''')

        # Storm threshold line at Kp=5
        storm_y = margin_top + chart_height - (5 / max_kp * chart_height)
        svg_parts.append(f'''  <line x1="{margin_left}" y1="{storm_y}" x2="{width - margin_right}" y2="{storm_y}" stroke="#f97316" stroke-width="1" stroke-dasharray="5,3" opacity="0.7"/>''')
        svg_parts.append(f'''  <text x="{width - margin_right - 2}" y="{storm_y - 3}" text-anchor="end" fill="#f97316" font-size="7" font-family="Arial">Storm</text>''')

        # Draw bars
        for i, (timestamp, kp_val) in enumerate(kp_history):
            x = margin_left + i * (bar_width + 4) + 2
            bar_height = (kp_val / max_kp) * chart_height
            y = margin_top + chart_height - bar_height
            color = self._get_kp_color(kp_val)

            svg_parts.append(f'''  <rect x="{x}" y="{y}" width="{bar_width}" height="{bar_height}" fill="{color}" rx="2"/>''')

            # Time label (shortened)
            try:
                time_str = timestamp.split()[1][:5] if ' ' in timestamp else timestamp[-5:]
            except:
                time_str = ""
            svg_parts.append(f'''  <text x="{x + bar_width/2}" y="{height - 8}" text-anchor="middle" fill="#666" font-size="6" font-family="Arial">{time_str}</text>''')

            # Kp value on top of bar
            svg_parts.append(f'''  <text x="{x + bar_width/2}" y="{y - 3}" text-anchor="middle" fill="#AAA" font-size="7" font-family="Arial">{kp_val:.0f}</text>''')

        # Legend
        legend_y = margin_top + 3
        colors = [('#22c55e', 'Quiet'), ('#eab308', 'Unsettled'), ('#f97316', 'Active'), ('#ef4444', 'Storm')]
        legend_x = margin_left
        for color, label in colors:
            svg_parts.append(f'''  <rect x="{legend_x}" y="{legend_y}" width="8" height="6" fill="{color}" rx="1"/>''')
            svg_parts.append(f'''  <text x="{legend_x + 10}" y="{legend_y + 5}" fill="#888" font-size="6" font-family="Arial">{label}</text>''')
            legend_x += 45

        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)

    def generate_solar_activity_svg(self, width=400, height=80):
        """Generate SVG showing current solar activity indicators"""
        current_data = self._fetch_current_data()
        
        svg_parts = []
        svg_parts.append(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" style="background-color: #1a1a2e;">''')

        # Title
        svg_parts.append(f'''  <text x="{width/2}" y="15" text-anchor="middle" fill="#CCCCCC" font-size="11" font-family="Arial">Solar Activity Status</text>''')

        # Three indicator boxes
        box_width = (width - 40) / 3
        box_height = 45
        box_y = 25

        indicators = [
            ('X-ray', current_data.get('xray_current', 'N/A'), self._get_xray_color(current_data.get('xray_current', 'N/A'))),
            ('Solar Flux', f"{current_data.get('solar_flux', 'N/A')} sfu", self._get_flux_color(current_data.get('solar_flux', 'N/A'))),
            ('Solar Wind', f"Bt {current_data.get('solar_wind_bt', 'N/A')} nT", self._get_wind_color(current_data.get('solar_wind_bt', 'N/A'))),
        ]

        for i, (label, value, color) in enumerate(indicators):
            x = 10 + i * (box_width + 10)
            # Box background
            svg_parts.append(f'''  <rect x="{x}" y="{box_y}" width="{box_width}" height="{box_height}" fill="#252540" rx="5" stroke="{color}" stroke-width="2"/>''')
            # Label
            svg_parts.append(f'''  <text x="{x + box_width/2}" y="{box_y + 15}" text-anchor="middle" fill="#888" font-size="9" font-family="Arial">{label}</text>''')
            # Value
            svg_parts.append(f'''  <text x="{x + box_width/2}" y="{box_y + 35}" text-anchor="middle" fill="{color}" font-size="12" font-family="Arial" font-weight="bold">{value}</text>''')

        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)

    def _get_xray_color(self, xray_class):
        """Get color based on X-ray class"""
        if not xray_class or xray_class == 'N/A':
            return '#888'
        if xray_class.startswith('X'):
            return '#ef4444'
        elif xray_class.startswith('M'):
            return '#f97316'
        elif xray_class.startswith('C'):
            return '#eab308'
        else:
            return '#22c55e'

    def _get_flux_color(self, flux):
        """Get color based on solar flux value"""
        try:
            flux_val = float(flux)
            if flux_val >= 150:
                return '#ef4444'
            elif flux_val >= 120:
                return '#f97316'
            elif flux_val >= 100:
                return '#eab308'
            else:
                return '#22c55e'
        except:
            return '#888'

    def _get_wind_color(self, bt):
        """Get color based on solar wind Bt"""
        try:
            bt_val = float(bt)
            if bt_val >= 20:
                return '#ef4444'
            elif bt_val >= 10:
                return '#f97316'
            elif bt_val >= 5:
                return '#eab308'
            else:
                return '#22c55e'
        except:
            return '#888'

    def format_forecast(self, include_charts=True):
        """Parse and format space weather forecast with optional charts"""
        forecast_text = self.pull_data()
        if forecast_text.startswith("error"):
            return f"❌ {forecast_text}"

        current_data = self._fetch_current_data()
        kp_values = self._parse_kp_index(forecast_text)

        current_kp = kp_values[0] if kp_values else 0
        peak_kp = max(kp_values) if kp_values else 0

        current_activity = self._get_activity_level(current_kp)
        peak_activity = self._get_activity_level(peak_kp)
        kp_emoji = self._get_activity_emoji(current_activity)

        xray_current = current_data.get('xray_current', 'N/A')
        xray_peak = current_data.get('xray_max_24h', 'N/A')

        if xray_peak != 'N/A' and isinstance(xray_peak, str):
            if xray_peak.startswith('X'):
                xray_emoji = '🔴'
            elif xray_peak.startswith('M'):
                xray_emoji = '🟠'
            elif xray_peak.startswith('C'):
                xray_emoji = '🟡'
            else:
                xray_emoji = '🟢'
        else:
            xray_emoji = '⚪'

        solar_flux = current_data.get('solar_flux', 'N/A')
        wind_bt = current_data.get('solar_wind_bt', 'N/A')
        wind_bz = current_data.get('solar_wind_bz', 'N/A')

        lines = []

        # Add charts if requested
        if include_charts:
            try:
                from svg_to_image import svg_to_email_image
                
                kp_chart = self.generate_kp_chart_svg()
                if kp_chart:
                    png_img = svg_to_email_image(kp_chart, alt_text="Kp Index Chart")
                    if png_img:
                        lines.append(png_img)
                    else:
                        lines.append('<div style="text-align: center;">')
                        lines.append(kp_chart)
                        lines.append('</div>')
                    lines.append("")

                solar_chart = self.generate_solar_activity_svg()
                if solar_chart:
                    png_img = svg_to_email_image(solar_chart, alt_text="Solar Activity Status")
                    if png_img:
                        lines.append(png_img)
                    else:
                        lines.append('<div style="text-align: center;">')
                        lines.append(solar_chart)
                        lines.append('</div>')
                    lines.append("")
            except ImportError:
                # Fallback to SVG if svg_to_image not available
                kp_chart = self.generate_kp_chart_svg()
                if kp_chart:
                    lines.append('<div style="text-align: center;">')
                    lines.append(kp_chart)
                    lines.append('</div>')
                    lines.append("")

                solar_chart = self.generate_solar_activity_svg()
                if solar_chart:
                    lines.append('<div style="text-align: center;">')
                    lines.append(solar_chart)
                    lines.append('</div>')
                    lines.append("")

        # Text summary
        if kp_values:
            lines.append(f"- {kp_emoji} **Kp Index**: {current_kp:.1f} (24h peak: {peak_kp:.1f} - {peak_activity})")
        else:
            lines.append(f"- ⚪ **Kp Index**: N/A")

        if xray_current != 'N/A' or xray_peak != 'N/A':
            lines.append(f"- {xray_emoji} **X-ray**: {xray_current} (24h peak: {xray_peak})")

        if solar_flux != 'N/A':
            lines.append(f"- 🌟 **Solar Flux**: {solar_flux} sfu")

        if wind_bt != 'N/A' and wind_bz != 'N/A':
            lines.append(f"- 🌪️ **Solar Wind**: Bt {wind_bt} nT, Bz {wind_bz} nT")

        return "\n".join(lines) if lines else "⚪ All quiet - no significant space weather activity"

if __name__=="__main__":
    rr = SpaceWeather()
    print(rr.format_forecast())
