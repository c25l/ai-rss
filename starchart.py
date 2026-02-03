#!/usr/bin/env python3
"""
Star Chart module - Generate SVG visualization of tonight's sky
Shows visible constellations, planets, and the moon as viewed from observer location.
"""
import ephem
import math
import os
from datetime import datetime, timedelta


class StarChart:
    """Generate an SVG star chart showing tonight's sky"""

    # Major bright stars with their RA/Dec (J2000) - subset for visualization
    # Format: name, RA (hours), Dec (degrees), magnitude
    BRIGHT_STARS = [
        ('Polaris', 2.53, 89.26, 2.0),
        ('Vega', 18.62, 38.78, 0.0),
        ('Capella', 5.28, 46.00, 0.1),
        ('Rigel', 5.24, -8.20, 0.1),
        ('Procyon', 7.66, 5.22, 0.4),
        ('Betelgeuse', 5.92, 7.41, 0.5),
        ('Altair', 19.85, 8.87, 0.8),
        ('Aldebaran', 4.60, 16.51, 0.9),
        ('Spica', 13.42, -11.16, 1.0),
        ('Antares', 16.49, -26.43, 1.1),
        ('Fomalhaut', 22.96, -29.62, 1.2),
        ('Deneb', 20.69, 45.28, 1.3),
        ('Regulus', 10.14, 11.97, 1.4),
        ('Castor', 7.58, 31.89, 1.6),
        ('Pollux', 7.76, 28.03, 1.2),
        ('Sirius', 6.75, -16.72, -1.5),
        ('Arcturus', 14.26, 19.18, -0.1),
        ('Canopus', 6.40, -52.70, -0.7),
    ]

    # Constellation lines (connecting bright stars) - simplified
    CONSTELLATION_LINES = {
        'Orion': [('Betelgeuse', 'Rigel')],
        'Big Dipper': [('Polaris', 'Polaris')],  # Just reference point
        'Summer Triangle': [('Vega', 'Altair'), ('Altair', 'Deneb'), ('Deneb', 'Vega')],
        'Gemini': [('Castor', 'Pollux')],
    }

    def __init__(self, width=500, height=500, lat=None, lon=None):
        self.width = width
        self.height = height
        self.cx = width / 2
        self.cy = height / 2
        self.radius = min(width, height) / 2 * 0.9

        # Observer location
        self.lat = lat or float(os.environ.get('LATITUDE', '40.1672'))
        self.lon = lon or float(os.environ.get('LONGITUDE', '-105.1019'))
        self.location_name = os.environ.get('LOCATION_NAME', 'Longmont, CO')

        # Set up observer
        self.observer = ephem.Observer()
        self.observer.lat = str(self.lat)
        self.observer.lon = str(self.lon)
        self.observer.elevation = 1500

    def _get_observation_time(self):
        """Get optimal observation time (around 10 PM local)"""
        now = datetime.now()
        # Set to 10 PM tonight
        obs_time = now.replace(hour=22, minute=0, second=0, microsecond=0)
        if now.hour >= 22:
            obs_time = obs_time  # Already past 10 PM, use now
        return obs_time

    def _ra_dec_to_alt_az(self, ra_hours, dec_deg, obs_time):
        """Convert RA/Dec to Alt/Az for observer at observation time"""
        # Create a fixed body at the RA/Dec position
        star = ephem.FixedBody()
        star._ra = ephem.hours(ra_hours * math.pi / 12)  # Convert hours to radians
        star._dec = ephem.degrees(dec_deg * math.pi / 180)  # Convert degrees to radians
        star._epoch = ephem.J2000

        # Set observer time
        self.observer.date = ephem.Date(obs_time)
        star.compute(self.observer)

        alt_deg = float(star.alt) * 180 / math.pi
        az_deg = float(star.az) * 180 / math.pi

        return (alt_deg, az_deg)

    def _alt_az_to_xy(self, alt_deg, az_deg):
        """
        Convert Alt/Az to XY on circular chart.
        Center = zenith (alt=90), edge = horizon (alt=0)
        North at top (az=0), East at right (az=90)
        """
        if alt_deg < 0:
            return None  # Below horizon

        # Distance from center: 0 at zenith, radius at horizon
        # Using stereographic projection for better representation
        r = self.radius * (1 - alt_deg / 90)

        # Azimuth angle (0=N at top, 90=E at right)
        az_rad = math.radians(az_deg)
        x = self.cx + r * math.sin(az_rad)
        y = self.cy - r * math.cos(az_rad)

        return (x, y)

    def _get_planet_positions(self, obs_time):
        """Get positions of visible planets"""
        planets = {
            'Mercury': (ephem.Mercury(), '#B5A642'),
            'Venus': (ephem.Venus(), '#E6E6FA'),
            'Mars': (ephem.Mars(), '#CD5C5C'),
            'Jupiter': (ephem.Jupiter(), '#DAA520'),
            'Saturn': (ephem.Saturn(), '#F4C430'),
        }

        visible = []
        self.observer.date = ephem.Date(obs_time)

        for name, (body, color) in planets.items():
            body.compute(self.observer)
            alt_deg = float(body.alt) * 180 / math.pi
            az_deg = float(body.az) * 180 / math.pi
            mag = float(body.mag)

            if alt_deg > 5:  # Above horizon with some margin
                visible.append({
                    'name': name,
                    'alt': alt_deg,
                    'az': az_deg,
                    'mag': mag,
                    'color': color
                })

        return visible

    def _get_moon_position(self, obs_time):
        """Get moon position and phase"""
        self.observer.date = ephem.Date(obs_time)
        moon = ephem.Moon(self.observer)

        alt_deg = float(moon.alt) * 180 / math.pi
        az_deg = float(moon.az) * 180 / math.pi
        phase = float(moon.phase)  # Illumination percentage

        if alt_deg > 0:
            return {
                'alt': alt_deg,
                'az': az_deg,
                'phase': phase
            }
        return None

    def generate_svg(self):
        """Generate SVG star chart visualization"""
        svg_parts = []
        obs_time = self._get_observation_time()

        # SVG header with dark background
        svg_parts.append(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width} {self.height}" style="background-color: #0a0a20;">
  <defs>
    <radialGradient id="skyGradient">
      <stop offset="0%" stop-color="#1a1a3a"/>
      <stop offset="100%" stop-color="#0a0a1a"/>
    </radialGradient>
    <radialGradient id="moonGlow">
      <stop offset="0%" stop-color="#FFFACD"/>
      <stop offset="70%" stop-color="#F0E68C"/>
      <stop offset="100%" stop-color="#F0E68C" stop-opacity="0"/>
    </radialGradient>
  </defs>''')

        # Sky circle with gradient
        svg_parts.append(f'''  <circle cx="{self.cx}" cy="{self.cy}" r="{self.radius}" fill="url(#skyGradient)" stroke="#334"/>''')

        # Cardinal direction labels
        directions = [('N', 0), ('E', 90), ('S', 180), ('W', 270)]
        for label, az in directions:
            az_rad = math.radians(az)
            x = self.cx + (self.radius + 15) * math.sin(az_rad)
            y = self.cy - (self.radius + 15) * math.cos(az_rad)
            svg_parts.append(f'''  <text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" dominant-baseline="middle" fill="#888" font-size="12" font-family="Arial" font-weight="bold">{label}</text>''')

        # Altitude circles (every 30°)
        for alt in [30, 60]:
            r = self.radius * (1 - alt / 90)
            svg_parts.append(f'''  <circle cx="{self.cx}" cy="{self.cy}" r="{r:.1f}" fill="none" stroke="#222244" stroke-width="0.5" stroke-dasharray="5,5"/>''')

        # Draw stars
        for name, ra, dec, mag in self.BRIGHT_STARS:
            alt, az = self._ra_dec_to_alt_az(ra, dec, obs_time)
            pos = self._alt_az_to_xy(alt, az)

            if pos:
                x, y = pos
                # Star size based on magnitude (brighter = larger)
                size = max(1, 4 - mag * 0.8)
                # Star brightness
                brightness = min(255, int(255 - mag * 30))
                color = f'rgb({brightness},{brightness},{brightness})'

                svg_parts.append(f'''  <circle cx="{x:.1f}" cy="{y:.1f}" r="{size:.1f}" fill="{color}"/>''')

                # Label for bright stars
                if mag < 1.0:
                    svg_parts.append(f'''  <text x="{x + size + 3:.1f}" y="{y + 3:.1f}" fill="#666" font-size="8" font-family="Arial">{name}</text>''')

        # Draw planets
        planets = self._get_planet_positions(obs_time)
        for planet in planets:
            pos = self._alt_az_to_xy(planet['alt'], planet['az'])
            if pos:
                x, y = pos
                # Planets are shown larger with their characteristic colors
                size = max(4, 6 - planet['mag'] * 0.5)
                svg_parts.append(f'''  <circle cx="{x:.1f}" cy="{y:.1f}" r="{size:.1f}" fill="{planet['color']}" stroke="#FFF" stroke-width="0.5"/>''')
                svg_parts.append(f'''  <text x="{x + size + 3:.1f}" y="{y + 3:.1f}" fill="{planet['color']}" font-size="9" font-family="Arial" font-weight="bold">{planet['name']}</text>''')

        # Draw moon if visible
        moon = self._get_moon_position(obs_time)
        if moon:
            pos = self._alt_az_to_xy(moon['alt'], moon['az'])
            if pos:
                x, y = pos
                moon_size = 12
                svg_parts.append(f'''  <circle cx="{x:.1f}" cy="{y:.1f}" r="{moon_size + 4}" fill="url(#moonGlow)" opacity="0.3"/>''')
                svg_parts.append(f'''  <circle cx="{x:.1f}" cy="{y:.1f}" r="{moon_size}" fill="#FFFACD"/>''')

                # Add phase indicator (simple shadow)
                if moon['phase'] < 50:
                    # Waxing - shadow on left
                    shadow_width = moon_size * (1 - moon['phase'] / 50)
                    svg_parts.append(f'''  <ellipse cx="{x - shadow_width/2:.1f}" cy="{y:.1f}" rx="{shadow_width:.1f}" ry="{moon_size}" fill="#0a0a20" opacity="0.8"/>''')

                svg_parts.append(f'''  <text x="{x:.1f}" y="{y + moon_size + 12:.1f}" text-anchor="middle" fill="#FFFACD" font-size="9" font-family="Arial">Moon ({moon['phase']:.0f}%)</text>''')

        # Title
        svg_parts.append(f'''  <text x="{self.cx}" y="20" text-anchor="middle" fill="#AAAAAA" font-size="14" font-family="Arial">Tonight's Sky - {self.location_name}</text>''')
        svg_parts.append(f'''  <text x="{self.cx}" y="36" text-anchor="middle" fill="#666666" font-size="10" font-family="Arial">{obs_time.strftime('%B %d, %Y')} ~10 PM</text>''')

        # Legend
        svg_parts.append(f'''  <text x="10" y="{self.height - 25}" fill="#666" font-size="8" font-family="Arial">● Stars  ● Planets</text>''')
        svg_parts.append(f'''  <text x="10" y="{self.height - 10}" fill="#666" font-size="8" font-family="Arial">Center = Zenith, Edge = Horizon</text>''')

        svg_parts.append('</svg>')

        return '\n'.join(svg_parts)

    def generate_markdown(self):
        """Generate markdown-embeddable SVG"""
        svg = self.generate_svg()
        return f'''<div style="text-align: center;">
{svg}
</div>'''


if __name__ == "__main__":
    chart = StarChart()
    print(chart.generate_svg())
