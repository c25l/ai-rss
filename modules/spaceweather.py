import requests
class SpaceWeather(object):
    def __init__(self):
        pass
    def pull_data(self):
        url="https://services.swpc.noaa.gov/text/3-day-forecast.txt"
        resp = requests.get(url)
        if resp.status_code == 200:
            return resp.text
        else:
            return "error fetching space weather"

if __name__=="__main__":
    rr = SpaceWeather()
    print(rr.pull_data())
