import requests
from pprint import pprint
from bs4    import BeautifulSoup

def get_directory():
    # Make request to get the route guide page
    url     = 'https://www.mountainproject.com/route-guide'
    content = requests.get(url).content
    soup    = BeautifulSoup(content)
    guide   = soup.find(id = 'route-guide')

    # Create a dictionary to store the directory
    directory = {}

    # Get the list of areas
    areas = [strong.find('a') for strong in guide.find_all('strong')]

    for area in areas:
        # Get the area name
        name = area.text

        # Get the area link
        link = area['href']

        # Save to directory
        directory[name] = link

    return directory