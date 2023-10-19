import requests
from bs4 import BeautifulSoup

def get_directory():
    url     = 'https://www.mountainproject.com/route-guide'
    content = requests.get(url).content
    soup    = BeautifulSoup(content)

    guide   = soup.find(id = 'route-guide')

    return guide