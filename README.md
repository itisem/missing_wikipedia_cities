# missing_wikipedia_cities

a small project i made to find the most populated cities that don't have a wikipedia article. if you are interested in how i got here, you might want to check out [my writeup](https://emily.bz/missing-wikipedia-cities).

## requirements

the only requirement to run this code is python >= 3.10

it is strongly recommended to create a [personal api token](https://api.wikimedia.org/wiki/Authentication#Personal_API_tokens) on wikipedia to avoid running into rate limits. without this, you are limited to 500 requests (25000 cities) per hour. you can either save this token in `wikipedia_token.txt`, or enter it in the program when prompted.