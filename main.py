import os.path
import webbrowser

import urllib.parse
from urllib.request import Request, urlopen

import json
import csv

from typing import TypedDict, TypeVar, Generator

########## config for default settings
mode = "geonames_manual" # one of: geonames_naive, geonames_manual
limit = 10 # how many cities to output
token_file = "wikipedia_token.txt" # where is the wikipedia access token located
geonames_file = "geonames.csv" # where is the downloaded geonames csv file located

########## typing

# city information, incl. lat and lng for mapping purposes
class CityInfo(TypedDict):
	name: str
	lat: float
	lng: float
	country: str
	pop: int

class MissingCityInfo(TypedDict):
	name: str
	index: int

########## every mode

# find cities from a list which are missing
def get_missing_cities(cities: list[str], token: str = "") -> list[MissingCityInfo]:
	# to query for multiple articles, wikipedia requests separation with |
	url_param = urllib.parse.quote("|".join(cities))
	query_url = f"https://en.wikipedia.org/w/api.php?action=query&format=json&titles={url_param}"
	missing_cities: list[MissingCityInfo] = []
	req = Request(query_url)
	if token != "":
		req.add_header("Authorization", f"Bearer {token}")
	with urlopen(req) as h:
		data = json.loads(h.read().decode())
		page_info = data["query"]["pages"]
		for k in page_info:
			# all missing articles have negative indices
			if(int(k) < 0):
				missing_cities.append({
					"name": page_info[k]["title"],
					# not the most efficient since indices keep increasing, but with a chunk size of 50, it's fine enough for now
					"index": cities.index(page_info[k]["title"])
				})
	return missing_cities

# chunks a list of cities to smaller bits for use in get_missing_cities
def chunk(cities: list[CityInfo], chunk_size = 50) -> Generator[list[CityInfo], None, None]:
	for i in range(0, len(cities), chunk_size):
		yield cities[i : i + chunk_size]

########## geonames only

# load data from a geonames csv file
def load_geonames(file: str = "geonames.csv") -> list[CityInfo]:
	with open(file, "r", encoding = "utf8") as f:
		data: list[CityInfo] = [{
			"name": x[2],
			"lat": float(x[4]),
			"lng": float(x[5]),
			"country": x[8],
			"pop": int(x[14])
		} for x in csv.reader(f, delimiter = "\t")]
		f.close()
		data.sort(key = lambda x: x["pop"], reverse = True)
		return data

# naively outputting the first n results from geonames
def geonames_naive(file: str, token: str, limit: int) -> list[CityInfo]:
	cities = load_geonames(file)
	no_article_cities: list[CityInfo] = []
	i = 0
	for city_chunk in chunk(cities):
		i += 1
		missing_cities = get_missing_cities([x["name"] for x in city_chunk], token)
		no_article_cities += [city_chunk[x["index"]] for x in missing_cities]
		missing_city_count = len(no_article_cities)
		print(f"Chunk {i}: {missing_city_count} / {limit}")
		if(len(no_article_cities) >= limit):
			break
	return no_article_cities[:limit]

# naively outputting the first n results from geonames
def geonames_manual(file: str, token: str, limit: int) -> list[CityInfo]:
	print("by default, all entries are assumed invalid. type \"y\" after a city name if it should be added to the list.")
	cities = load_geonames(file)
	no_article_cities: list[CityInfo] = []
	i = 0
	for city_chunk in chunk(cities):
		i += 1
		missing_cities = get_missing_cities([x["name"] for x in city_chunk], token)
		for city in missing_cities:
			should_add = input(f"{city['name']}: ")
			if(should_add.lower() == "y" or should_add.lower() == "yes"):
				no_article_cities.append(city_chunk[city["index"]])
		missing_city_count = len(no_article_cities)
		print(f"Chunk {i}: {missing_city_count} / {limit}")
		if(len(no_article_cities) >= limit):
			break
	return no_article_cities[:limit]

if __name__ == "__main__":

	# handling wikipedia api tokens
	wikipedia_token = ""
	# if there is a token file, load its contents
	if(os.path.isfile(token_file)):
		with open(token_file, "r") as f:
			wikipedia_token = f.read()
	# otherwise, prompt for a token to avoid rate limits
	else:
		print("you have not specified a personal api token. this will almost certainly result in getting rate limited.")
		token_request_response = input("do you want to create an api token now (default: yes)?")
		if(token_request_response.lower() == "n" or token_request_response.lower() == "no"):
			# do nothing. no need for a second warning
			pass
		else:
			webbrowser.open("https://api.wikimedia.org/wiki/Authentication#Personal_API_tokens", new = 2) # 2 = new tab
			print("once you created a token, paste it below, and press enter")
			wikipedia_token = input("")
			with open(token_file, "w") as f:
				f.write(wikipedia_token)

	# decide what mode to run in
	match mode:
		case "geonames_naive":
			cities = geonames_naive(geonames_file, wikipedia_token, limit)
			print(cities)
		case "geonames_manual":
			cities = geonames_manual(geonames_file, wikipedia_token, limit)
			print(cities)
		case _:
			print("Invalid mode")