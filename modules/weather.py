import requests
import json
class Weather(object):
    def __init__(self):
        pass
    def pull_data(self):
        #url="https://forecast.weather.gov/MapClick.php?CityName=Longmont&state=CO&site=BOU&textField1=40.1728&textField2=-105.112&e=0"
        #url="https://api.weather.gov/points/40.1728,-105.112"
        url="https://api.weather.gov/gridpoints/BOU/60,81/forecast"
        resp = requests.get(url)
        if resp.status_code == 200:
            return json.dumps([xx['name']+": " + xx['detailedForecast'] for xx in json.loads(resp.text).get("properties",{}).get("periods",[])[0:7]])
        
        else:
            return "error fetching weather"

if __name__=="__main__":
    rr = Weather()
    print(rr.pull_data())
