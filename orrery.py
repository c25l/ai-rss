#!/usr/bin/env python3
"""
Orrery module - Generate SVG visualization of the solar system
Shows current planetary positions as viewed from above the solar system.
Includes all planets, minor objects, and pointers to deep sky objects.
"""
import ephem
import math
from datetime import datetime


class Orrery:
    """Generate an SVG orrery showing current planetary positions"""

    # All planets with colors and orbital slot (using constant spacing)
    PLANETS = {
        'Mercury': {'color': '#B5A642', 'slot': 1, 'body': ephem.Mercury, 'size': 3},
        'Venus': {'color': '#E6E6FA', 'slot': 2, 'body': ephem.Venus, 'size': 5},
        'Earth': {'color': '#4169E1', 'slot': 3, 'body': None, 'size': 5},
        'Mars': {'color': '#CD5C5C', 'slot': 4, 'body': ephem.Mars, 'size': 4},
        'Jupiter': {'color': '#DAA520', 'slot': 6, 'body': ephem.Jupiter, 'size': 10},
        'Saturn': {'color': '#F4C430', 'slot': 7, 'body': ephem.Saturn, 'size': 9},
        'Uranus': {'color': '#87CEEB', 'slot': 8, 'body': ephem.Uranus, 'size': 7},
        'Neptune': {'color': '#4169E1', 'slot': 9, 'body': ephem.Neptune, 'size': 7},
    }

    # Minor objects (asteroid belt slot 5, outer objects slot 10)
    MINOR_OBJECTS = {
        'Ceres': {'color': '#8B8989', 'slot': 5, 'size': 2},  # Asteroid belt
        'Pluto': {'color': '#DEB887', 'slot': 10, 'size': 2},
    }

    # Deep sky pointers (RA in hours, Dec in degrees for J2000)
    DEEP_SKY = {
        'Galactic Center': {'ra': 17.76, 'dec': -29.0, 'color': '#FFD700', 'symbol': '*'},
        'Alpha Centauri': {'ra': 14.66, 'dec': -60.83, 'color': '#FFFFFF', 'symbol': '+'},
        'Andromeda (M31)': {'ra': 0.71, 'dec': 41.27, 'color': '#C0C0FF', 'symbol': 'o'},
    }

    def __init__(self, width=500, height=500):
        self.width = width
        self.height = height
        self.cx = width / 2
        self.cy = height / 2
        # Max radius for outermost orbit (slot 10)
        self.max_radius = min(width, height) / 2 * 0.75
        # Spacing per slot
        self.slot_spacing = self.max_radius / 11  # 11 slots (0=sun, 1-10=orbits)

    def _get_heliocentric_position(self, body_func):
        """
        Get heliocentric longitude and distance for a planet.
        Returns (longitude_degrees, distance_au)
        """
        if body_func is None:
            return (0, 1.0)

        body = body_func()
        body.compute(ephem.now())

        hlon = float(body.hlon) * 180 / math.pi
        sun_dist = float(body.sun_distance)

        return (hlon, sun_dist)

    def _get_earth_position(self):
        """Get Earth's heliocentric longitude"""
        sun = ephem.Sun()
        sun.compute(ephem.now())
        earth_hlon = (float(sun.hlon) * 180 / math.pi + 180) % 360
        return (earth_hlon, 1.0)

    def _get_minor_object_position(self, name):
        """Get approximate position for minor objects using ephem database"""
        try:
            if name == 'Ceres':
                # Ceres orbital elements in ephem XEphem format:
                # name,type,inclination,long_asc_node,arg_perihelion,semi_major_axis,
                # eccentricity,mean_anomaly,mean_daily_motion,epoch,equinox,H_mag,G_slope
                body = ephem.readdb("Ceres,e,10.59,80.33,73.60,2.77,0.214,0.0758,352.23,01/01/2020,2000,H 3.34,0.12")
            elif name == 'Pluto':
                body = ephem.Pluto()
            else:
                return (0, 0)
            
            body.compute(ephem.now())
            hlon = float(body.hlon) * 180 / math.pi
            return (hlon, float(body.sun_distance))
        except:
            # Fallback: return a fixed position
            return (45 if name == 'Ceres' else 270, 2.77 if name == 'Ceres' else 39.5)

    def _slot_to_radius(self, slot):
        """Convert orbit slot to SVG radius"""
        return slot * self.slot_spacing

    def _polar_to_cartesian(self, angle_deg, radius):
        """Convert polar (angle, radius) to SVG cartesian coordinates"""
        angle_rad = math.radians(angle_deg - 90)  # 0° at top
        x = self.cx + radius * math.cos(angle_rad)
        y = self.cy + radius * math.sin(angle_rad)
        return (x, y)

    def _ra_dec_to_angle(self, ra_hours, dec_deg):
        """
        Convert RA/Dec to an angle for the orrery edge pointer.
        This is approximate - we convert RA to ecliptic longitude.
        """
        # Simplified conversion: RA hours to degrees (15° per hour)
        # This gives the approximate direction in the sky
        angle = ra_hours * 15
        return angle

    def generate_svg(self):
        """Generate SVG orrery visualization"""
        svg_parts = []

        # SVG header with dark background
        svg_parts.append(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width} {self.height}" style="background-color: #0a0a1a;">
  <defs>
    <radialGradient id="sunGlow">
      <stop offset="0%" stop-color="#FFD700"/>
      <stop offset="50%" stop-color="#FFA500"/>
      <stop offset="100%" stop-color="#FF4500" stop-opacity="0"/>
    </radialGradient>
    <marker id="arrowhead" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
      <polygon points="0 0, 6 3, 0 6" fill="#888"/>
    </marker>
  </defs>''')

        # Title
        now = datetime.now()
        svg_parts.append(f'''  <text x="{self.cx}" y="18" text-anchor="middle" fill="#CCCCCC" font-size="12" font-family="Arial">Solar System - {now.strftime('%B %d, %Y')}</text>''')

        # Draw orbit circles (constant spacing)
        for slot in range(1, 11):
            radius = self._slot_to_radius(slot)
            opacity = 0.4 if slot <= 4 else 0.3  # Inner planets slightly more visible
            svg_parts.append(f'''  <circle cx="{self.cx}" cy="{self.cy}" r="{radius:.1f}" fill="none" stroke="#333355" stroke-width="0.5" stroke-dasharray="3,3" opacity="{opacity}"/>''')

        # Draw asteroid belt region (between Mars slot 4 and Jupiter slot 6)
        belt_inner = self._slot_to_radius(4.5)
        belt_outer = self._slot_to_radius(5.5)
        svg_parts.append(f'''  <circle cx="{self.cx}" cy="{self.cy}" r="{(belt_inner + belt_outer)/2:.1f}" fill="none" stroke="#555566" stroke-width="{belt_outer - belt_inner:.1f}" stroke-dasharray="1,3" opacity="0.3"/>''')

        # Draw Sun at center
        svg_parts.append(f'''  <circle cx="{self.cx}" cy="{self.cy}" r="12" fill="url(#sunGlow)"/>
  <circle cx="{self.cx}" cy="{self.cy}" r="6" fill="#FFD700"/>''')

        # Draw planets
        for name, data in self.PLANETS.items():
            if name == 'Earth':
                hlon, _ = self._get_earth_position()
            else:
                hlon, _ = self._get_heliocentric_position(data['body'])

            radius = self._slot_to_radius(data['slot'])
            x, y = self._polar_to_cartesian(hlon, radius)
            size = data['size']

            # Draw planet
            svg_parts.append(f'''  <circle cx="{x:.1f}" cy="{y:.1f}" r="{size}" fill="{data['color']}"/>''')

            # Add Saturn's rings
            if name == 'Saturn':
                svg_parts.append(f'''  <ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{size * 1.8}" ry="{size * 0.4}" fill="none" stroke="{data['color']}" stroke-width="1.5" opacity="0.7"/>''')

            # Add Uranus's tilted rings
            if name == 'Uranus':
                svg_parts.append(f'''  <ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{size * 0.4}" ry="{size * 1.4}" fill="none" stroke="{data['color']}" stroke-width="0.8" opacity="0.5"/>''')

            # Label (smaller font for outer planets)
            font_size = 8 if data['slot'] >= 6 else 9
            label_offset = size + 6
            svg_parts.append(f'''  <text x="{x:.1f}" y="{y + label_offset:.1f}" text-anchor="middle" fill="#AAAAAA" font-size="{font_size}" font-family="Arial">{name}</text>''')

        # Draw minor objects
        for name, data in self.MINOR_OBJECTS.items():
            hlon, _ = self._get_minor_object_position(name)
            radius = self._slot_to_radius(data['slot'])
            x, y = self._polar_to_cartesian(hlon, radius)
            size = data['size']

            # Draw as smaller circle
            svg_parts.append(f'''  <circle cx="{x:.1f}" cy="{y:.1f}" r="{size}" fill="{data['color']}" opacity="0.8"/>''')
            # Smaller label
            svg_parts.append(f'''  <text x="{x:.1f}" y="{y + size + 5:.1f}" text-anchor="middle" fill="#888888" font-size="7" font-family="Arial">{name}</text>''')

        # Draw deep sky pointers at edge
        edge_radius = self.max_radius + 15
        pointer_length = 25
        for name, data in self.DEEP_SKY.items():
            angle = self._ra_dec_to_angle(data['ra'], data['dec'])
            
            # Arrow start and end points
            start_r = edge_radius
            end_r = edge_radius + pointer_length
            x1, y1 = self._polar_to_cartesian(angle, start_r)
            x2, y2 = self._polar_to_cartesian(angle, end_r)
            
            # Draw arrow line
            svg_parts.append(f'''  <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{data['color']}" stroke-width="1.5" marker-end="url(#arrowhead)" opacity="0.8"/>''')
            
            # Symbol and label at arrow tip
            lx, ly = self._polar_to_cartesian(angle, end_r + 8)
            svg_parts.append(f'''  <text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" fill="{data['color']}" font-size="10">{data['symbol']}</text>''')
            
            # Name label (shortened for space)
            short_name = name.split('(')[0].strip()[:12]
            nlx, nly = self._polar_to_cartesian(angle, end_r + 18)
            svg_parts.append(f'''  <text x="{nlx:.1f}" y="{nly:.1f}" text-anchor="middle" fill="#888888" font-size="6" font-family="Arial">{short_name}</text>''')

        # Legend
        svg_parts.append(f'''  <text x="10" y="{self.height - 20}" fill="#666666" font-size="7" font-family="Arial">● Planets  ○ Minor Objects  → Deep Sky</text>''')
        svg_parts.append(f'''  <text x="10" y="{self.height - 10}" fill="#666666" font-size="7" font-family="Arial">View from above ecliptic plane</text>''')

        svg_parts.append('</svg>')

        return '\n'.join(svg_parts)

    def generate_markdown(self):
        """Generate markdown-embeddable SVG"""
        svg = self.generate_svg()
        # Wrap in HTML for markdown embedding
        return f'''<div style="text-align: center;">
{svg}
</div>'''

    def generate_email_image(self):
        """Generate email-friendly PNG image from SVG"""
        try:
            from svg_to_image import svg_to_email_image, get_converter_status
            
            # Check if converter is available
            status = get_converter_status()
            if not status['any_available']:
                print("ERROR: No SVG to PNG converter available. Install cairosvg: pip install cairosvg")
                print("  On Ubuntu/Debian, also run: sudo apt-get install libcairo2-dev")
                return ""
            
            svg = self.generate_svg()
            result = svg_to_email_image(svg, alt_text="Solar System Orrery")
            if not result:
                print("ERROR: SVG to PNG conversion returned empty result for orrery")
            return result
        except ImportError as e:
            print(f"ERROR: Could not import svg_to_image: {e}")
            return ""
        except Exception as e:
            print(f"ERROR: Could not generate orrery PNG: {e}")
            import traceback
            traceback.print_exc()
            return ""


if __name__ == "__main__":
    orrery = Orrery()
    print(orrery.generate_svg())
