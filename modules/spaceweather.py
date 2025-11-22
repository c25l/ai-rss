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
        # Download and embed the space weather overview image
        img_url = "https://services.swpc.noaa.gov/images/swx-overview-small.gif"
        txt_url = "https://services.swpc.noaa.gov/text/3-day-forecast.txt"
        try:
            txt_resp = requests.get(txt_url, timeout=10)
            if txt_resp.status_code != 200:
                return "error fetching space weather"
            text = txt_resp.text
            return text
            img_resp = requests.get(img_url, timeout=10)
            if img_resp.status_code == 200:
                img_base64 = base64.b64encode(img_resp.content).decode('utf-8')
                img_tag = f"<img src='data:image/gif;base64,{img_base64}' alt='Space Weather Overview'/>"
            else:
                img_tag = "<p>Could not load space weather image</p>"
        except Exception as e:
            img_tag = f"<p>Error loading image: {e}</p>"

        html_parts = ["<div style='font-family:sans-serif;'>"]
        html_parts.append(f"<div>{img_tag}</div>")
        return "\n".join(html_parts+["</div>"])
            
        resp = requests.get(url)
        if resp.status_code == 200:
            text = resp.text
            
            # Parse numerical data
            kp_values = self._parse_kp_index(text)
            solar_flux = self._parse_solar_flux(text)
            
            html_parts = ["<div style='font-family:sans-serif;'>"]
            html_parts.append("<div><src='https://services.swpc.noaa.gov/images/swx-overview-small.gif' alt='Space Weather Overview'/></div>")
            return "\n".append(html_parts+["</div>"])
            # Current conditions summary
            if kp_values:
                current_kp = kp_values[0] if kp_values else 0
                activity = self._get_activity_level(int(current_kp))
                color = self._get_kp_color(int(current_kp))
                
                html_parts.append(f"""
<div style='display:inline-block;margin:10px;padding:12px;border:2px solid {color};border-radius:8px;text-align:center;background-color:{color}20;'>
<div style='font-size:24px;font-weight:bold;color:{color};'>Kp {current_kp:.1f}</div>
<div style='font-size:18px;color:#666;'>{activity}</div>
</div>""")
            
            # Solar flux info
            if solar_flux:
                avg_flux = sum(solar_flux) // len(solar_flux)
                html_parts.append(f"""
<div style='display:inline-block;margin:10px;padding:12px;border:1px solid #ddd;border-radius:8px;text-align:center;'>
<div style='font-size:20px;font-weight:bold;'>☀️ Solar Flux</div>
<div style='font-size:22px;color:#f59e0b;'>{avg_flux} sfu</div>
</div>""")
            
            # # Kp forecast chart
            # if kp_values:
            #     chart = self._create_kp_chart(kp_values[:8])  # Show up to 8 periods
            #     html_parts.append(f"<div style='margin:15px 0;'><strong>3-Day Kp Forecast:</strong><br/>{chart}</div>")
            
            # # Activity indicators
            # html_parts.append("<div style='margin:10px 0;font-size:14px;'>")
            # html_parts.append("<strong>Activity Levels:</strong> ")
            # html_parts.append("<span style='color:#22c55e;'>●</span> Quiet (0-2) ")
            # html_parts.append("<span style='color:#eab308;'>●</span> Unsettled (3-4) ")
            # html_parts.append("<span style='color:#f97316;'>●</span> Active (5-6) ")
            # html_parts.append("<span style='color:#ef4444;'>●</span> Storm (7-8) ")
            # html_parts.append("<span style='color:#7c2d12;'>●</span> Severe (9)")
            # html_parts.append("</div>")
            
            html_parts.append("</div>")
            return "".join(html_parts)
        else:
            return "error fetching space weather"

if __name__=="__main__":
    rr = SpaceWeather()
    print(rr.pull_data())
