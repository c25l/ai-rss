#!/usr/bin/env python3
"""
Direct PNG generation using Pillow.
Generates visualizations directly as PNG images without requiring Cairo or SVG conversion.
This is a pure Python solution that works on any system with Pillow installed.
"""
import base64
import io
import math
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

# Try to load a nicer font, fall back to default
def get_font(size=12, bold=False):
    """Get a font, falling back to default if custom fonts unavailable"""
    try:
        # Try common system fonts
        font_names = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/System/Library/Fonts/Helvetica.ttc',
            'arial.ttf',
        ]
        if bold:
            font_names = [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
                'arialbd.ttf',
            ] + font_names
        
        for font_name in font_names:
            try:
                return ImageFont.truetype(font_name, size)
            except (IOError, OSError):
                continue
    except:
        pass
    
    # Fall back to default font
    return ImageFont.load_default()


def image_to_base64_data_uri(img: Image.Image) -> str:
    """Convert PIL Image to base64 data URI"""
    buffer = io.BytesIO()
    img.save(buffer, format='PNG', optimize=True)
    base64_png = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{base64_png}"


def image_to_email_html(img: Image.Image, alt_text: str = "Visualization") -> str:
    """Convert PIL Image to HTML img tag with base64 data"""
    data_uri = image_to_base64_data_uri(img)
    return f'<div style="text-align: center; margin: 15px 0;"><img src="{data_uri}" alt="{alt_text}" style="width: 100%; max-width: 500px; display: block; margin: 10px auto;" /></div>'


class OrreryPNG:
    """Generate PNG orrery visualization directly using Pillow"""
    
    # Planet data: color, orbit slot (1-10), size
    PLANETS = {
        'Mercury': {'color': '#B5A642', 'slot': 1, 'size': 6},
        'Venus': {'color': '#E6E6FA', 'slot': 2, 'size': 10},
        'Earth': {'color': '#4169E1', 'slot': 3, 'size': 10},
        'Mars': {'color': '#CD5C5C', 'slot': 4, 'size': 8},
        'Jupiter': {'color': '#DAA520', 'slot': 6, 'size': 20},
        'Saturn': {'color': '#F4C430', 'slot': 7, 'size': 18},
        'Uranus': {'color': '#87CEEB', 'slot': 8, 'size': 14},
        'Neptune': {'color': '#4169E1', 'slot': 9, 'size': 14},
    }
    
    MINOR_OBJECTS = {
        'Ceres': {'color': '#8B8989', 'slot': 5, 'size': 4},
        'Pluto': {'color': '#DEB887', 'slot': 10, 'size': 4},
    }
    
    def __init__(self, width=500, height=500):
        self.width = width
        self.height = height
        self.cx = width // 2
        self.cy = height // 2
        self.max_radius = min(width, height) // 2 - 40
        self.slot_spacing = self.max_radius // 11
        
    def _get_planet_angle(self, name):
        """Get approximate heliocentric angle for a planet"""
        try:
            import ephem
            if name == 'Earth':
                sun = ephem.Sun()
                sun.compute(ephem.now())
                return (float(sun.hlon) * 180 / math.pi + 180) % 360
            elif name in ['Ceres', 'Pluto']:
                if name == 'Pluto':
                    body = ephem.Pluto()
                else:
                    return 45  # Approximate for Ceres
                body.compute(ephem.now())
                return float(body.hlon) * 180 / math.pi
            else:
                body_map = {
                    'Mercury': ephem.Mercury,
                    'Venus': ephem.Venus,
                    'Mars': ephem.Mars,
                    'Jupiter': ephem.Jupiter,
                    'Saturn': ephem.Saturn,
                    'Uranus': ephem.Uranus,
                    'Neptune': ephem.Neptune,
                }
                if name in body_map:
                    body = body_map[name]()
                    body.compute(ephem.now())
                    return float(body.hlon) * 180 / math.pi
        except:
            pass
        
        # Fallback: distribute evenly
        all_objects = list(self.PLANETS.keys()) + list(self.MINOR_OBJECTS.keys())
        if name in all_objects:
            idx = all_objects.index(name)
            return (idx * 36) % 360
        return 0
    
    def _polar_to_xy(self, angle_deg, radius):
        """Convert polar to cartesian coordinates"""
        angle_rad = math.radians(angle_deg - 90)
        x = self.cx + radius * math.cos(angle_rad)
        y = self.cy + radius * math.sin(angle_rad)
        return int(x), int(y)
    
    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def generate_png(self) -> Image.Image:
        """Generate PNG image of the orrery"""
        # Create dark background
        img = Image.new('RGB', (self.width, self.height), color=(10, 10, 26))
        draw = ImageDraw.Draw(img)
        
        # Title
        title_font = get_font(14)
        title = f"Solar System - {datetime.now().strftime('%B %d, %Y')}"
        bbox = draw.textbbox((0, 0), title, font=title_font)
        text_width = bbox[2] - bbox[0]
        draw.text((self.cx - text_width // 2, 10), title, fill=(200, 200, 200), font=title_font)
        
        # Draw orbit circles
        for slot in range(1, 11):
            radius = slot * self.slot_spacing
            opacity = 80 if slot <= 4 else 60
            draw.ellipse(
                [self.cx - radius, self.cy - radius, self.cx + radius, self.cy + radius],
                outline=(51, 51, 85, opacity),
                width=1
            )
        
        # Draw asteroid belt (slot 5)
        belt_radius = int(5 * self.slot_spacing)
        for i in range(0, 360, 5):
            angle_rad = math.radians(i)
            variation = (i * 17) % 10 - 5  # Pseudo-random variation
            r = belt_radius + variation
            x = int(self.cx + r * math.cos(angle_rad))
            y = int(self.cy + r * math.sin(angle_rad))
            draw.point((x, y), fill=(85, 85, 102))
        
        # Draw Sun
        sun_radius = 15
        for r in range(sun_radius + 10, sun_radius, -1):
            alpha = int(255 * (1 - (r - sun_radius) / 10))
            color = (255, 165, 0, alpha)
            draw.ellipse(
                [self.cx - r, self.cy - r, self.cx + r, self.cy + r],
                fill=(255, 200, 50) if r == sun_radius else None,
                outline=color if r > sun_radius else None
            )
        draw.ellipse(
            [self.cx - sun_radius, self.cy - sun_radius, self.cx + sun_radius, self.cy + sun_radius],
            fill=(255, 215, 0)
        )
        
        # Draw planets
        label_font = get_font(10)
        for name, data in self.PLANETS.items():
            angle = self._get_planet_angle(name)
            radius = data['slot'] * self.slot_spacing
            x, y = self._polar_to_xy(angle, radius)
            size = data['size']
            color = self._hex_to_rgb(data['color'])
            
            draw.ellipse([x - size, y - size, x + size, y + size], fill=color)
            
            # Saturn's rings
            if name == 'Saturn':
                ring_w = int(size * 1.8)
                ring_h = int(size * 0.4)
                draw.ellipse([x - ring_w, y - ring_h, x + ring_w, y + ring_h], outline=color, width=2)
            
            # Uranus's rings (vertical)
            if name == 'Uranus':
                ring_w = int(size * 0.4)
                ring_h = int(size * 1.4)
                draw.ellipse([x - ring_w, y - ring_h, x + ring_w, y + ring_h], outline=color, width=1)
            
            # Label
            draw.text((x - 15, y + size + 3), name, fill=(170, 170, 170), font=label_font)
        
        # Draw minor objects
        small_font = get_font(8)
        for name, data in self.MINOR_OBJECTS.items():
            angle = self._get_planet_angle(name)
            radius = data['slot'] * self.slot_spacing
            x, y = self._polar_to_xy(angle, radius)
            size = data['size']
            color = self._hex_to_rgb(data['color'])
            
            draw.ellipse([x - size, y - size, x + size, y + size], fill=color)
            draw.text((x - 10, y + size + 2), name, fill=(136, 136, 136), font=small_font)
        
        # Legend
        legend_font = get_font(9)
        draw.text((10, self.height - 25), "● Planets  ○ Minor Objects", fill=(102, 102, 102), font=legend_font)
        draw.text((10, self.height - 12), "View from above ecliptic", fill=(102, 102, 102), font=legend_font)
        
        return img
    
    def generate_email_image(self) -> str:
        """Generate email-friendly HTML with embedded PNG"""
        try:
            img = self.generate_png()
            return image_to_email_html(img, "Solar System Orrery")
        except Exception as e:
            print(f"ERROR generating orrery PNG: {e}")
            import traceback
            traceback.print_exc()
            return ""


class StarChartPNG:
    """Generate PNG star chart visualization directly using Pillow"""
    
    # Bright stars: name, RA (hours), Dec (degrees), magnitude
    BRIGHT_STARS = [
        ('Sirius', 6.75, -16.72, -1.46),
        ('Vega', 18.62, 38.78, 0.03),
        ('Capella', 5.28, 46.0, 0.08),
        ('Rigel', 5.24, -8.2, 0.13),
        ('Betelgeuse', 5.92, 7.41, 0.42),
        ('Altair', 19.85, 8.87, 0.77),
        ('Aldebaran', 4.60, 16.51, 0.85),
        ('Spica', 13.42, -11.16, 0.97),
        ('Pollux', 7.76, 28.03, 1.14),
        ('Deneb', 20.69, 45.28, 1.25),
    ]
    
    # Planet colors
    PLANET_COLORS = {
        'Mercury': '#B5A642',
        'Venus': '#FFFACD',
        'Mars': '#CD5C5C',
        'Jupiter': '#DAA520',
        'Saturn': '#F4C430',
    }
    
    def __init__(self, width=500, height=500, location_name="Observer Location"):
        self.width = width
        self.height = height
        self.cx = width // 2
        self.cy = height // 2
        self.radius = min(width, height) // 2 - 40
        self.location_name = location_name
    
    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _get_visible_planets(self):
        """Get currently visible planets with positions"""
        planets = []
        try:
            import ephem
            observer = ephem.Observer()
            observer.lat = '40.17'  # Default latitude
            observer.lon = '-105.1'  # Default longitude
            observer.date = ephem.now()
            
            planet_bodies = [
                ('Mercury', ephem.Mercury()),
                ('Venus', ephem.Venus()),
                ('Mars', ephem.Mars()),
                ('Jupiter', ephem.Jupiter()),
                ('Saturn', ephem.Saturn()),
            ]
            
            for name, body in planet_bodies:
                body.compute(observer)
                alt = float(body.alt) * 180 / math.pi
                az = float(body.az) * 180 / math.pi
                if alt > 0:  # Above horizon
                    planets.append({
                        'name': name,
                        'alt': alt,
                        'az': az,
                        'color': self.PLANET_COLORS.get(name, '#FFFFFF')
                    })
        except:
            # Fallback: show some planets at fixed positions
            planets = [
                {'name': 'Jupiter', 'alt': 45, 'az': 180, 'color': '#DAA520'},
                {'name': 'Saturn', 'alt': 30, 'az': 220, 'color': '#F4C430'},
            ]
        
        return planets
    
    def _alt_az_to_xy(self, alt, az):
        """Convert altitude/azimuth to x,y on circular chart"""
        # Distance from center based on altitude (90° = center, 0° = edge)
        r = self.radius * (90 - alt) / 90
        # Azimuth: 0 = N (top), 90 = E (right), etc.
        angle_rad = math.radians(az - 90)
        x = self.cx + r * math.cos(angle_rad)
        y = self.cy + r * math.sin(angle_rad)
        return int(x), int(y)
    
    def generate_png(self) -> Image.Image:
        """Generate PNG image of the star chart"""
        # Create dark blue gradient background
        img = Image.new('RGB', (self.width, self.height), color=(10, 10, 32))
        draw = ImageDraw.Draw(img)
        
        # Draw gradient for sky
        for r in range(self.radius, 0, -1):
            # Darker at edge, lighter at center
            intensity = int(20 + (self.radius - r) * 10 / self.radius)
            color = (intensity, intensity, intensity + 20)
            draw.ellipse(
                [self.cx - r, self.cy - r, self.cx + r, self.cy + r],
                outline=color
            )
        
        # Draw horizon circle
        draw.ellipse(
            [self.cx - self.radius, self.cy - self.radius, 
             self.cx + self.radius, self.cy + self.radius],
            outline=(100, 100, 120),
            width=2
        )
        
        # Draw cardinal directions
        title_font = get_font(14)
        directions = [('N', 0), ('E', 90), ('S', 180), ('W', 270)]
        for label, az in directions:
            angle_rad = math.radians(az - 90)
            x = int(self.cx + (self.radius + 20) * math.cos(angle_rad))
            y = int(self.cy + (self.radius + 20) * math.sin(angle_rad))
            draw.text((x - 5, y - 7), label, fill=(150, 150, 180), font=title_font)
        
        # Title
        title = f"Tonight's Sky - {self.location_name}"
        bbox = draw.textbbox((0, 0), title, font=title_font)
        text_width = bbox[2] - bbox[0]
        draw.text((self.cx - text_width // 2, 8), title, fill=(180, 180, 200), font=title_font)
        
        # Date
        small_font = get_font(10)
        date_str = datetime.now().strftime('%B %d, %Y')
        bbox = draw.textbbox((0, 0), date_str, font=small_font)
        text_width = bbox[2] - bbox[0]
        draw.text((self.cx - text_width // 2, 26), date_str, fill=(120, 120, 150), font=small_font)
        
        # Draw some stars (simplified - just show bright stars at approximate positions)
        star_font = get_font(8)
        for name, ra, dec, mag in self.BRIGHT_STARS:
            # Simplified: use RA as azimuth proxy, Dec as altitude proxy
            # This is not astronomically accurate but gives a visual representation
            az = (ra * 15) % 360  # RA hours to degrees
            alt = 45 + dec * 0.5  # Rough approximation
            
            if 10 < alt < 85:  # Only show if reasonably visible
                x, y = self._alt_az_to_xy(alt, az)
                
                # Star size based on magnitude
                size = max(1, int(4 - mag))
                brightness = min(255, int(255 - mag * 30))
                color = (brightness, brightness, brightness)
                
                draw.ellipse([x - size, y - size, x + size, y + size], fill=color)
                
                # Label bright stars
                if mag < 0.5:
                    draw.text((x + size + 2, y - 4), name, fill=(150, 150, 150), font=star_font)
        
        # Draw visible planets
        planets = self._get_visible_planets()
        planet_font = get_font(9)
        for planet in planets:
            x, y = self._alt_az_to_xy(planet['alt'], planet['az'])
            color = self._hex_to_rgb(planet['color'])
            size = 6
            
            # Draw planet with glow
            draw.ellipse([x - size - 2, y - size - 2, x + size + 2, y + size + 2], 
                        fill=(color[0]//3, color[1]//3, color[2]//3))
            draw.ellipse([x - size, y - size, x + size, y + size], fill=color)
            draw.text((x + size + 3, y - 5), planet['name'], fill=color, font=planet_font)
        
        # Legend
        legend_font = get_font(9)
        draw.text((10, self.height - 25), "● Stars  ● Planets", fill=(120, 120, 140), font=legend_font)
        draw.text((10, self.height - 12), "Center = Zenith, Edge = Horizon", fill=(100, 100, 120), font=legend_font)
        
        return img
    
    def generate_email_image(self) -> str:
        """Generate email-friendly HTML with embedded PNG"""
        try:
            img = self.generate_png()
            return image_to_email_html(img, "Tonight's Star Chart")
        except Exception as e:
            print(f"ERROR generating star chart PNG: {e}")
            import traceback
            traceback.print_exc()
            return ""


if __name__ == "__main__":
    print("Testing direct PNG generation...")
    
    # Test Orrery
    orrery = OrreryPNG()
    result = orrery.generate_email_image()
    if result:
        print(f"✓ Orrery PNG: {len(result)} characters")
    else:
        print("✗ Orrery PNG failed")
    
    # Test Star Chart
    chart = StarChartPNG(location_name="Longmont, CO")
    result = chart.generate_email_image()
    if result:
        print(f"✓ Star Chart PNG: {len(result)} characters")
    else:
        print("✗ Star Chart PNG failed")
