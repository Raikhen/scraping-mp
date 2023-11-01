import re
import json
import requests
from pprint import pprint
from bs4    import BeautifulSoup

'''
TODO
    - Get photos
    - Get comments
    - Get the "extra" info (the stuff that you need to click on the + to get)
'''

def parse_area_details(raw_details):
    # Create a dictionary to store the area details
    details = {}
    rows    = raw_details.find_all('tr')

    # Get area elevation (NOTE: only works if we always use the same unit)
    raw_elevation = rows[0].find_all('td')[1].text
    details['elevation'] = int(re.sub(',', '', raw_elevation.split(' ')[0]))

    # Get area location
    location_td     = rows[1].find_all('td')[1]
    coordinates     = re.sub('[^\d^.^,^-]', '', location_td.text)
    google_map_url  = location_td.find_all('a')[0]['href']
    area_map_url    = location_td.find_all('a')[1]['href']

    details['location'] = {
        'coordinates': coordinates,
        'google_map_url': google_map_url,
        'area_map_url': area_map_url
    }

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

    # Return area details
    return details

def get_area(url):
    # Make request to get the area page
    content = requests.get(url).content
    soup    = BeautifulSoup(content, features='html.parser')

    # Create a dictionary to store the area
    area = { 'url': url }

    # Get sidebar
    sidebar = soup.find(class_ = 'mp-sidebar')
    
    # Get area type (whether it contains areas or routes)
    sidebar_contains = sidebar.find('h3').text.split(' ')[0].lower()
    area['contains'] = sidebar_contains

    # Get area items (areas or routes)
    sidebar_items = sidebar.find(class_ = 'max-height').find_all('a')
    area['items'] = { item.text: item['href'] for item in sidebar_items }

    # Get area name
    area['name'] = soup.find('h1').contents[0].strip()

    # Get area details
    raw_details = soup.find(class_ = 'description-details')
    details     = parse_area_details(raw_details)
    area.update(details)

    # Get area description and directions
    main_content            = soup.find(class_ = 'main-content')
    sections                = main_content.find_all(class_ = 'fr-view')
    area['description_txt'] = sections[0].get_text(separator = '\n\n')
    area['directions_txt']  = sections[1].get_text(separator = '\n\n')

    return area

# Test
cannon = get_area('https://www.mountainproject.com/area/107340274/cannon-cliff')
print(json.dumps(cannon, sort_keys = True, indent = 4))