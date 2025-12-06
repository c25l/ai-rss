#!/usr/bin/env python3
"""
Astronomy module - Fetch real-time astronomical data for tonight's sky
"""
import requests
from datetime import datetime, timedelta
import os
import claude


class Astronomy:
    """Fetch and format astronomical visibility data"""

    def __init__(self):
        # Default to Longmont, CO
        self.lat = float(os.environ.get('LATITUDE', '40.1672'))
        self.lon = float(os.environ.get('LONGITUDE', '-105.1019'))
        self.location_name = os.environ.get('LOCATION_NAME', 'Longmont, CO')

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

    def _get_iss_passes(self):
        """Get visible ISS passes for tonight"""
        try:
            # N-2T0 API for ISS passes (more reliable than open-notify)
            # We'll use open-notify as fallback
            url = "http://api.open-notify.org/iss-pass.json"
            params = {
                'lat': self.lat,
                'lon': self.lon,
                'n': 5  # Get next 5 passes
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('response'):
                    passes = []
                    now = datetime.now()
                    tonight_end = now.replace(hour=23, minute=59, second=59)

                    for p in data['response']:
                        pass_time = datetime.fromtimestamp(p['risetime'])
                        # Only include passes that are tonight
                        if now <= pass_time <= tonight_end:
                            passes.append({
                                'time': pass_time.strftime('%I:%M %p'),
                                'duration': p['duration']
                            })
                    return passes[:3]  # Return up to 3 passes tonight
            return []
        except Exception as e:
            print(f"Error fetching ISS passes: {e}")
            return []

    def _get_moon_phase(self):
        """Calculate current moon phase (approximate)"""
        try:
            # Simple moon phase calculation
            # For more accuracy, could use an astronomy library like ephem or skyfield
            now = datetime.now()

            # Known new moon: 2025-01-29
            known_new_moon = datetime(2025, 1, 29, 12, 0, 0)
            synodic_month = 29.53058867  # days

            days_since_new = (now - known_new_moon).total_seconds() / 86400
            phase = (days_since_new % synodic_month) / synodic_month

            # Calculate illumination percentage
            illumination = (1 - abs((phase - 0.5) * 2)) * 100

            # Determine phase name
            if phase < 0.0625 or phase >= 0.9375:
                phase_name = "New Moon"
            elif 0.0625 <= phase < 0.1875:
                phase_name = "Waxing Crescent"
            elif 0.1875 <= phase < 0.3125:
                phase_name = "First Quarter"
            elif 0.3125 <= phase < 0.4375:
                phase_name = "Waxing Gibbous"
            elif 0.4375 <= phase < 0.5625:
                phase_name = "Full Moon"
            elif 0.5625 <= phase < 0.6875:
                phase_name = "Waning Gibbous"
            elif 0.6875 <= phase < 0.8125:
                phase_name = "Last Quarter"
            else:
                phase_name = "Waning Crescent"

            return {
                'phase': phase_name,
                'illumination': int(illumination)
            }
        except Exception as e:
            print(f"Error calculating moon phase: {e}")
            return None

    def pull_data(self):
        """Gather all astronomical data"""
        data = {
            'date': datetime.now().strftime('%B %d, %Y'),
            'location': self.location_name,
            'sun_moon': self._get_sun_moon_data(),
            'iss_passes': self._get_iss_passes(),
            'moon_phase': self._get_moon_phase()
        }
        return data

    def format_output(self):
        """Format astronomical data into readable text for Claude to enhance"""
        data = self.pull_data()

        output = f"""# Tonight's Sky Data for {data['location']} ({data['date']})

## Sun & Twilight Times
"""
        if data['sun_moon']:
            output += f"- Sunset: {data['sun_moon']['sunset']}\n"
            output += f"- Civil twilight ends: {data['sun_moon']['civil_twilight_end']} (sky dark enough for bright stars)\n"
            output += f"- Astronomical twilight ends: {data['sun_moon']['astronomical_twilight_end']} (fully dark sky)\n"

        output += "\n## Moon\n"
        if data['moon_phase']:
            output += f"- Phase: {data['moon_phase']['phase']} ({data['moon_phase']['illumination']}% illuminated)\n"

        output += "\n## ISS Passes\n"
        if data['iss_passes']:
            for i, iss_pass in enumerate(data['iss_passes'], 1):
                output += f"- Pass {i}: {iss_pass['time']} (visible for ~{iss_pass['duration']} seconds)\n"
        else:
            output += "- No visible ISS passes tonight\n"

        output += f"""
## Additional Context
Location coordinates: {self.lat}°N, {self.lon}°W
Date: {datetime.now().strftime('%Y-%m-%d')}
Season: Early December (Winter sky constellations)
"""

        # Now use Claude to add planet positions and deep sky objects
        prompt = f"""Using the data below and your astronomical knowledge, create a concise "Tonight's Sky Guide" for stargazing.

{output}

Please provide:
1. **Planets**: Which planets are visible tonight, when, and where to look (be specific about direction and time)
2. **Moon**: Summarize the moon data above (phase, illumination, best viewing time)
3. **ISS Passes**: Summarize the ISS passes above (if any)
4. **Constellations & Deep Sky**: What constellations and notable objects are visible in early December
5. **Special Events**: Any meteor showers or special astronomical events happening now

IMPORTANT: Format with <br/> tags at the end of each line for proper HTML email rendering.
Each bullet point or section should end with <br/>
Be specific about timing and directions. Maximum 10 lines total.
"""

        result = claude.Claude().generate(prompt)

        # Ensure result has <br/> tags - if not, add them
        if result and '<br/>' not in result:
            # Add <br/> at the end of each line
            lines = result.strip().split('\n')
            result = '<br/>'.join(line for line in lines if line.strip())

        return result


if __name__ == "__main__":
    astro = Astronomy()
    print(astro.format_output())
