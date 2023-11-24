import requests
import config

url = "https://tasty.p.rapidapi.com/recipes/auto-complete"

querystring = {"prefix":"chicken soup"}

headers = {
	"X-RapidAPI-Key": config.food_api_credentials["X-RapidAPI-Key"],
	"X-RapidAPI-Host": config.food_api_credentials["X-RapidAPI-Host"]
}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())