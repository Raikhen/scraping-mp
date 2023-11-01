import re
import json
import roman
import requests
from pprint import pprint
from bs4    import BeautifulSoup

def parse_route_details(raw_details):
    # Create a dictionary to store the route details
    details = {}
    rows    = raw_details.find_all('tr')

    # Get route types, length, and # of pitches
    raw_types = rows[0].find_all('td')[1].text.strip().split(', ')
    # details['types'] = raw_types

    if raw_types[-1].split(' ')[0] == 'Grade':
        details['grade'] = roman.fromRoman(raw_types[-1].split(' ')[1])

    # Get first ascent info
    details['first_ascent'] = rows[1].find_all('td')[1].text

    # Get page views
    raw_views = rows[2].find_all('td')[1].text
    raw_views = re.sub('[^\d^·]', '', raw_views).split('·')

    details['page_views'] = {
        'total': raw_views[0],
        'per_month': raw_views[1]
    }

    # Get "shared by"
    raw_shared_by   = rows[3].find_all('td')[1]
    raw_uploader    = raw_shared_by.find_all('a')[0]
    upload_date     = raw_shared_by.contents[2].strip()[3:]

    details['shared_by'] = {
        'name': raw_uploader.text,
        'url': raw_uploader['href'],
        'upload_date': upload_date
    }

    # Get admins
    raw_admins          = rows[4].find_all('td')[1].find_all('a')
    details['admins']   = [ { 'name': admin.text, 'url': admin['href'] } for admin in raw_admins ]

    return details

def get_route(url):
    # Make request to get the route page
    content = requests.get(url).content
    soup    = BeautifulSoup(content, features='html.parser')

    # Create a dictionary to store the route
    route = { 'url': url }

    # Get route name
    route['name'] = soup.find('h1').contents[0].strip()

    # Get route grade
    route['grade'] = soup.find(class_ = 'rateYDS').contents[0].strip()

    # Get safety and aid grades
    other_ratings_element   = soup.find(class_ = 'mr-2').contents[-1]
    other_ratings_text      = other_ratings_element.text.strip()
    route['other_ratings']  = other_ratings_text

    '''
    TODO: break down other ratings into
        - Aid
        - Ice
        - Mixed
        - Snow
        - Safety
    '''

    # Get area description, location, and protection
    sections_container  = soup.find_all(class_ = 'col-xs-12')[0].find_all('div')

    for div in sections_container:
        if div.find('h2') != None:
            section_name = div.find('h2').text.strip().lower()
            section_text = div.find(class_ = 'fr-view').get_text(separator = '\n\n')
            route[section_name] = section_text
        else:
            # TODO: include access notes and other warnings
            pass

    # Get area details
    raw_details = soup.find(class_ = 'description-details')
    details     = parse_route_details(raw_details)
    route.update(details)

    return route

# Test
moby = get_route('https://www.mountainproject.com/route/105884815/moby-grape')
print(json.dumps(moby, sort_keys = True, indent = 4))

# Test
# vertigo = get_route('https://www.mountainproject.com/route/105888753/vertigo')
# print(json.dumps(vertigo, sort_keys = True, indent = 4))

# Test
# clippidy = get_route('https://www.mountainproject.com/route/105888037/clip-a-dee-doo-dah')
# print(json.dumps(clippidy, sort_keys = True, indent = 4))