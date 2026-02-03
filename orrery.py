#!/usr/bin/env python3
"""
Orrery module - Generate SVG visualization of the solar system
Shows current planetary positions as viewed from above the solar system.
"""
import ephem
import math
from datetime import datetime


class Orrery:
    """Generate an SVG orrery showing current planetary positions"""

    # Approximate orbital periods in days (for animation, not needed for static)
    # Semi-major axes in AU
    PLANETS = {
        'Mercury': {'color': '#B5A642', 'orbit_au': 0.387, 'body': ephem.Mercury},
        'Venus': {'color': '#E6E6FA', 'orbit_au': 0.723, 'body': ephem.Venus},
        'Earth': {'color': '#4169E1', 'orbit_au': 1.0, 'body': None},  # We're viewing from Earth's perspective
        'Mars': {'color': '#CD5C5C', 'orbit_au': 1.524, 'body': ephem.Mars},
        'Jupiter': {'color': '#DAA520', 'orbit_au': 5.203, 'body': ephem.Jupiter},
        'Saturn': {'color': '#F4C430', 'orbit_au': 9.537, 'body': ephem.Saturn},
    }

    def __init__(self, width=400, height=400):
        self.width = width
        self.height = height
        self.cx = width / 2
        self.cy = height / 2
        # Scale factor: map 10 AU to fit within radius
        self.scale = min(width, height) / 2 * 0.85 / 10  # 10 AU = 85% of half-width

    def _get_heliocentric_position(self, body_func):
        """
        Get heliocentric longitude and distance for a planet.
        Returns (longitude_degrees, distance_au)
        """
        if body_func is None:
            return (0, 1.0)  # Earth at 0° reference

        body = body_func()
        body.compute(ephem.now())

        # Get heliocentric longitude (sun-centered, ecliptic coordinates)
        hlon = float(body.hlon) * 180 / math.pi  # Convert to degrees
        # Get heliocentric distance
        sun_dist = float(body.sun_distance)  # in AU

        return (hlon, sun_dist)

    def _get_earth_position(self):
        """Get Earth's heliocentric longitude by computing Sun's apparent position"""
        sun = ephem.Sun()
        sun.compute(ephem.now())
        # Earth is opposite the Sun's apparent position
        earth_hlon = (float(sun.hlon) * 180 / math.pi + 180) % 360
        return (earth_hlon, 1.0)

    def _polar_to_cartesian(self, angle_deg, distance_au):
        """Convert polar (angle, distance) to SVG cartesian coordinates"""
        angle_rad = math.radians(angle_deg - 90)  # Rotate so 0° is at top
        # Apply logarithmic scaling for outer planets to fit better
        # Inner planets (< 2 AU): linear scale
        # Outer planets (> 2 AU): compressed scale
        if distance_au <= 2:
            scaled_dist = distance_au * self.scale * 15  # Boost inner planets
        else:
            # Logarithmic compression for outer planets
            scaled_dist = (2 * 15 + math.log(distance_au / 2 + 1) * 40) * self.scale

        x = self.cx + scaled_dist * math.cos(angle_rad)
        y = self.cy + scaled_dist * math.sin(angle_rad)
        return (x, y)

    def _orbit_radius(self, distance_au):
        """Get orbit circle radius for a given AU distance"""
        if distance_au <= 2:
            return distance_au * self.scale * 15
        else:
            return (2 * 15 + math.log(distance_au / 2 + 1) * 40) * self.scale

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
  </defs>''')

        # Title
        now = datetime.now()
        svg_parts.append(f'''  <text x="{self.cx}" y="20" text-anchor="middle" fill="#CCCCCC" font-size="14" font-family="Arial">Solar System - {now.strftime('%B %d, %Y')}</text>''')

        # Draw orbit circles (dashed)
        for name, data in self.PLANETS.items():
            radius = self._orbit_radius(data['orbit_au'])
            svg_parts.append(f'''  <circle cx="{self.cx}" cy="{self.cy}" r="{radius:.1f}" fill="none" stroke="#333355" stroke-width="0.5" stroke-dasharray="3,3"/>''')

        # Draw Sun at center
        svg_parts.append(f'''  <circle cx="{self.cx}" cy="{self.cy}" r="15" fill="url(#sunGlow)"/>
  <circle cx="{self.cx}" cy="{self.cy}" r="8" fill="#FFD700"/>''')

        # Get Earth position first (for reference)
        earth_hlon, _ = self._get_earth_position()

        # Draw planets
        for name, data in self.PLANETS.items():
            if name == 'Earth':
                hlon, dist = self._get_earth_position()
            else:
                hlon, dist = self._get_heliocentric_position(data['body'])

            x, y = self._polar_to_cartesian(hlon, data['orbit_au'])

            # Planet size based on actual relative size (simplified)
            sizes = {'Mercury': 3, 'Venus': 5, 'Earth': 5, 'Mars': 4, 'Jupiter': 10, 'Saturn': 9}
            size = sizes.get(name, 5)

            # Draw planet
            svg_parts.append(f'''  <circle cx="{x:.1f}" cy="{y:.1f}" r="{size}" fill="{data['color']}"/>''')

            # Add Saturn's rings
            if name == 'Saturn':
                svg_parts.append(f'''  <ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{size * 1.8}" ry="{size * 0.4}" fill="none" stroke="{data['color']}" stroke-width="1.5" opacity="0.7"/>''')

            # Label
            label_offset = size + 8
            svg_parts.append(f'''  <text x="{x:.1f}" y="{y + label_offset:.1f}" text-anchor="middle" fill="#AAAAAA" font-size="9" font-family="Arial">{name}</text>''')

        # Add legend
        svg_parts.append(f'''  <text x="10" y="{self.height - 10}" fill="#666666" font-size="8" font-family="Arial">View from above ecliptic plane</text>''')

        svg_parts.append('</svg>')

        return '\n'.join(svg_parts)

    def generate_markdown(self):
        """Generate markdown-embeddable SVG"""
        svg = self.generate_svg()
        # Wrap in HTML for markdown embedding
        return f'''<div style="text-align: center;">
{svg}
</div>'''


if __name__ == "__main__":
    orrery = Orrery()
    print(orrery.generate_svg())
