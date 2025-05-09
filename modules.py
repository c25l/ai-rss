import noaa_sdk
import yfinance as yf
from datetime import datetime, timedelta

#Weather
class Weather:
	def info(generate):
		n = noaa_sdk.NOAA()
		fct = n.get_forecasts("80503","US")
		out = []
		for ii,jj in [[0,23],[24,47],[48,71]]:
			data =[[xx["temperature"],xx["shortForecast"]] for xx in fct if ii<xx["number"]<jj]
			maxt = max(xx[0] for xx in data)
			mint = min(xx[0] for xx in data)
			current = [xx[1] for xx in data]
			condition = generate("I'm going to provide you a list of weather conditions near me for a period of several hours. Which one is the most serious? please express this to me with a single weather related emoji. I cant take anything beyond this single emoji so please dont explain--I trust your judgment.\n"+"\n".join(current))
			dayname = (datetime.today()+timedelta(hours=ii+1)).strftime('%a')
			out.append(f'- {dayname}: {condition} {mint}°F-{maxt}°F')
			if ii == 0:
				out = [f"# {condition} Weather"] + out
		return "\n".join(out)

#Stocks
class Stocks:
	def quotes():
		tcks = ["DJIA","comp","msft","nvda","aapl"]
		tks = yf.tickers.Tickers(tcks).tickers

		out = []
		for xx,yy in tks.items():
			yy=yy.history(period="1d")
			diff = (yy.Close -yy.Open).iloc[0]
			pct = diff/yy.Open.iloc[0]
			tcolor ='green' if diff>0 else 'red'
			char="\u2191" if diff>0 else "\u2193"
			today = f"""- {xx} ${yy.Close.iloc[0]:.2f} <span style="color:{tcolor}">{char} ${diff:.2f} ({pct:.2%})</span>"""
			out.append(today)
			if xx.lower() == "msft":
				icon = "📈" if pct>0 else "📉"
				out = [f"# {icon} Stocks"] + out
		return "\n".join(out)

