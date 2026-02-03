#!/usr/bin/env python3
"""
Astronomy module - Fetch real-time astronomical data for tonight's sky
"""
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
        """Get sunrise, sunset, and astronomical twilight times using ephem"""
        try:
            self.observer.date = ephem.now()
            sun = ephem.Sun()

            # Get sunset
            sunset = self.observer.next_setting(sun).datetime()

            # For twilight, we need to set the horizon to -6° (civil) and -18° (astronomical)
            # Save original horizon
            original_horizon = self.observer.horizon

            # Civil twilight (sun 6° below horizon)
            self.observer.horizon = '-6'
            civil_twilight_end = self.observer.next_setting(sun, use_center=True).datetime()

            # Astronomical twilight (sun 18° below horizon)
            self.observer.horizon = '-18'
            astronomical_twilight_end = self.observer.next_setting(sun, use_center=True).datetime()

            # Restore original horizon
            self.observer.horizon = original_horizon

            # Convert to local timezone (MST is UTC-7)
            offset = timedelta(hours=-7)
            return {
                'sunset': (sunset + offset).strftime('%I:%M %p'),
                'civil_twilight_end': (civil_twilight_end + offset).strftime('%I:%M %p'),
                'astronomical_twilight_end': (astronomical_twilight_end + offset).strftime('%I:%M %p')
            }
        except Exception as e:
            print(f"Error calculating sun/moon data: {e}")
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
        """Get planets visible during dark hours tonight with rise/set times"""
        try:
            # Get dark hours (after astronomical twilight)
            sun_moon = self._get_sun_moon_data()
            if not sun_moon:
                return []

            # Parse astronomical twilight end time (when it's truly dark)
            # This is in local time like "06:20 PM"
            now = datetime.now()
            twilight_str = sun_moon['astronomical_twilight_end']
            twilight_time = datetime.strptime(f"{now.date()} {twilight_str}", "%Y-%m-%d %I:%M %p")

            # Dark hours: from twilight end tonight until twilight start tomorrow morning (~6 AM)
            dark_start = twilight_time
            dark_end = (now + timedelta(days=1)).replace(hour=6, minute=0, second=0, microsecond=0)

            # Convert to UTC for ephem (MST is UTC-7)
            dark_start_utc = dark_start + timedelta(hours=7)
            dark_end_utc = dark_end + timedelta(hours=7)

            # Use current time as reference
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

                try:
                    # Get next rise and set times
                    next_rise = self.observer.next_rising(planet).datetime()
                    next_set = self.observer.next_setting(planet).datetime()

                    # Check if planet is above horizon during dark hours
                    # Sample the planet's altitude at dark_start and dark_end
                    self.observer.date = ephem.Date(dark_start_utc)
                    planet.compute(self.observer)
                    alt_at_dark_start = float(planet.alt) * 180 / 3.14159

                    self.observer.date = ephem.Date(dark_end_utc)
                    planet.compute(self.observer)
                    alt_at_dark_end = float(planet.alt) * 180 / 3.14159

                    # Also check at midnight
                    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                    midnight_utc = midnight + timedelta(hours=7)
                    self.observer.date = ephem.Date(midnight_utc)
                    planet.compute(self.observer)
                    alt_at_midnight = float(planet.alt) * 180 / 3.14159

                    # Reset observer to now
                    self.observer.date = ephem.now()
                    planet.compute(self.observer)

                    # Only include if planet is above horizon at any point during dark hours
                    if alt_at_dark_start > 0 or alt_at_midnight > 0 or alt_at_dark_end > 0:
                        # Calculate position at transit (highest point)
                        transit_time = self.observer.next_transit(planet)
                        self.observer.date = transit_time
                        planet.compute(self.observer)

                        # Get altitude and azimuth at transit
                        alt_deg = float(planet.alt) * 180 / 3.14159
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

                        # Reset observer
                        self.observer.date = ephem.now()

                        visible.append({
                            'name': name,
                            'max_altitude': int(alt_deg),
                            'direction': direction,
                            'rise': (next_rise + offset).strftime('%I:%M %p'),
                            'set': (next_set + offset).strftime('%I:%M %p'),
                            'magnitude': float(planet.mag)
                        })
                except Exception as e:
                    pass

            # Sort by max altitude (highest first)
            visible.sort(key=lambda p: p['max_altitude'], reverse=True)
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

    def format_output(self, include_visualizations=False):
        """Format astronomical data into readable text
        
        Args:
            include_visualizations: If True, include orrery and star chart SVGs
        """
        data = self.pull_data()

        output = []
        output.append(f"**Tonight's Sky for {data['location']}** ({data['date']})")

        # Sun & Twilight
        if data['sun_moon']:
            output.append(f"- **Sunset:** {data['sun_moon']['sunset']} | **Dark sky:** {data['sun_moon']['astronomical_twilight_end']}")

        # Moon
        if data['moon_phase']:
            output.append(f"- **Moon:** {data['moon_phase']['phase']} ({data['moon_phase']['illumination']}% illuminated) | Rise: {data['moon_phase']['rise']}, Set: {data['moon_phase']['set']}")

        # Planets
        if data['planets']:
            output.append(f"\n**Visible Planets:**")
            for planet in data['planets'][:5]:  # Show top 5
                output.append(f"- **{planet['name']}** - {planet['direction']}, max {planet['max_altitude']}° | Rise: {planet['rise']}, Set: {planet['set']}")
        else:
            output.append(f"\n- **Planets:** None visible tonight")

        # Add visualizations if requested
        if include_visualizations:
            try:
                from orrery import Orrery
                from starchart import StarChart
                
                output.append("\n### Solar System Overview")
                orrery = Orrery()
                output.append(orrery.generate_markdown())
                
                output.append("\n### Tonight's Star Chart")
                starchart = StarChart(lat=self.lat, lon=self.lon)
                output.append(starchart.generate_markdown())
            except Exception as e:
                output.append(f"\n*Visualization generation error: {e}*")

        return '\n'.join(output)

    def get_orrery_svg(self):
        """Generate orrery SVG visualization"""
        from orrery import Orrery
        return Orrery().generate_svg()

    def get_starchart_svg(self):
        """Generate star chart SVG visualization"""
        from starchart import StarChart
        return StarChart(lat=self.lat, lon=self.lon).generate_svg()


if __name__ == "__main__":
    astro = Astronomy()
    print(astro.format_output(include_visualizations=True))
