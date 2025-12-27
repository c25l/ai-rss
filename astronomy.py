#!/usr/bin/env python3
"""
Astronomy module - Fetch real-time astronomical data for tonight's sky
"""
import requests
import ephem
from datetime import datetime, timedelta
import os


class Astronomy:
    """Fetch and format astronomical visibility data"""

    def __init__(self):
        # Default to Longmont, CO
        self.lat = float(os.environ.get('LATITUDE', '40.1672'))
        self.lon = float(os.environ.get('LONGITUDE', '-105.1019'))
        self.location_name = os.environ.get('LOCATION_NAME', 'Longmont, CO')

        # Create observer
        self.observer = ephem.Observer()
        self.observer.lat = str(self.lat)
        self.observer.lon = str(self.lon)
        self.observer.elevation = 1500  # meters (approximate for Longmont)

    def _get_sun_moon_data(self):
        """Get sunrise, sunset, and astronomical twilight times"""
        try:
            url = "https://api.sunrise-sunset.org/json"
            params = {
                'lat': self.lat,
                'lng': self.lon,
                'formatted': 0,
                'date': datetime.now().strftime('%Y-%m-%d')
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('status') == 'OK':
                results = data['results']
                # Convert UTC to local time (MST is UTC-7)
                sunset = datetime.fromisoformat(results['sunset'].replace('Z', '+00:00'))
                civil_twilight_end = datetime.fromisoformat(results['civil_twilight_end'].replace('Z', '+00:00'))
                astronomical_twilight_end = datetime.fromisoformat(results['astronomical_twilight_end'].replace('Z', '+00:00'))

                # Convert to local timezone (approximate MST)
                offset = timedelta(hours=-7)
                return {
                    'sunset': (sunset + offset).strftime('%I:%M %p'),
                    'civil_twilight_end': (civil_twilight_end + offset).strftime('%I:%M %p'),
                    'astronomical_twilight_end': (astronomical_twilight_end + offset).strftime('%I:%M %p')
                }
        except Exception as e:
            print(f"Error fetching sun/moon data: {e}")
            return None

    def _get_moon_phase(self):
        """Calculate current moon phase using ephem"""
        try:
            self.observer.date = ephem.now()
            moon = ephem.Moon(self.observer)

            # Get illumination percentage
            illumination = int(moon.phase)

            # Calculate phase name based on moon age
            previous_new = ephem.previous_new_moon(ephem.now())
            next_new = ephem.next_new_moon(ephem.now())
            lunation = (ephem.now() - previous_new) / (next_new - previous_new)

            # Determine phase name
            if lunation < 0.0625 or lunation >= 0.9375:
                phase_name = "New Moon"
            elif 0.0625 <= lunation < 0.1875:
                phase_name = "Waxing Crescent"
            elif 0.1875 <= lunation < 0.3125:
                phase_name = "First Quarter"
            elif 0.3125 <= lunation < 0.4375:
                phase_name = "Waxing Gibbous"
            elif 0.4375 <= lunation < 0.5625:
                phase_name = "Full Moon"
            elif 0.5625 <= lunation < 0.6875:
                phase_name = "Waning Gibbous"
            elif 0.6875 <= lunation < 0.8125:
                phase_name = "Last Quarter"
            else:
                phase_name = "Waning Crescent"

            # Get moonrise and moonset
            try:
                moonrise = self.observer.next_rising(moon).datetime()
                moonset = self.observer.next_setting(moon).datetime()
                offset = timedelta(hours=-7)
                moonrise_local = (moonrise + offset).strftime('%I:%M %p')
                moonset_local = (moonset + offset).strftime('%I:%M %p')
            except:
                moonrise_local = "N/A"
                moonset_local = "N/A"

            return {
                'phase': phase_name,
                'illumination': illumination,
                'rise': moonrise_local,
                'set': moonset_local
            }
        except Exception as e:
            print(f"Error calculating moon phase: {e}")
            return None

    def _get_visible_planets(self):
        """Get visible planets for tonight"""
        try:
            self.observer.date = ephem.now()

            planets = {
                'Mercury': ephem.Mercury(),
                'Venus': ephem.Venus(),
                'Mars': ephem.Mars(),
                'Jupiter': ephem.Jupiter(),
                'Saturn': ephem.Saturn()
            }

            visible = []
            offset = timedelta(hours=-7)

            for name, planet in planets.items():
                planet.compute(self.observer)

                # Check if planet is above horizon at night
                # Get next rising and setting
                try:
                    next_rise = self.observer.next_rising(planet).datetime()
                    next_set = self.observer.next_setting(planet).datetime()

                    # Convert altitude to degrees
                    alt_deg = float(planet.alt) * 180 / 3.14159

                    # Planet is visible if altitude > 0 (above horizon)
                    if alt_deg > 0:
                        # Get azimuth (direction)
                        az_deg = float(planet.az) * 180 / 3.14159

                        # Convert azimuth to cardinal direction
                        if az_deg < 22.5 or az_deg >= 337.5:
                            direction = "N"
                        elif 22.5 <= az_deg < 67.5:
                            direction = "NE"
                        elif 67.5 <= az_deg < 112.5:
                            direction = "E"
                        elif 112.5 <= az_deg < 157.5:
                            direction = "SE"
                        elif 157.5 <= az_deg < 202.5:
                            direction = "S"
                        elif 202.5 <= az_deg < 247.5:
                            direction = "SW"
                        elif 247.5 <= az_deg < 292.5:
                            direction = "W"
                        else:
                            direction = "NW"

                        visible.append({
                            'name': name,
                            'altitude': int(alt_deg),
                            'direction': direction,
                            'rise': (next_rise + offset).strftime('%I:%M %p'),
                            'set': (next_set + offset).strftime('%I:%M %p'),
                            'magnitude': float(planet.mag)
                        })
                except:
                    pass

            # Sort by altitude (highest first)
            visible.sort(key=lambda p: p['altitude'], reverse=True)
            return visible

        except Exception as e:
            print(f"Error calculating planetary positions: {e}")
            return []

    def pull_data(self):
        """Gather all astronomical data"""
        data = {
            'date': datetime.now().strftime('%B %d, %Y'),
            'location': self.location_name,
            'sun_moon': self._get_sun_moon_data(),
            'moon_phase': self._get_moon_phase(),
            'planets': self._get_visible_planets()
        }
        return data

    def format_output(self):
        """Format astronomical data into readable text"""
        data = self.pull_data()

        output = []
        output.append(f"**Tonight's Sky for {data['location']}** ({data['date']})<br/>")

        # Sun & Twilight
        if data['sun_moon']:
            output.append(f"**Sunset:** {data['sun_moon']['sunset']} | **Dark sky:** {data['sun_moon']['astronomical_twilight_end']}<br/>")

        # Moon
        if data['moon_phase']:
            output.append(f"**Moon:** {data['moon_phase']['phase']} ({data['moon_phase']['illumination']}% illuminated) | Rise: {data['moon_phase']['rise']}, Set: {data['moon_phase']['set']}<br/>")

        # Planets
        if data['planets']:
            output.append(f"<br/>**Visible Planets:**<br/>")
            for planet in data['planets'][:5]:  # Show top 5
                output.append(f"• **{planet['name']}** - {planet['direction']}, {planet['altitude']}° above horizon<br/>")
        else:
            output.append(f"<br/>**Planets:** None visible tonight<br/>")

        return '\n'.join(output)


if __name__ == "__main__":
    astro = Astronomy()
    print(astro.format_output())
