import re
import json
import requests
import dateparser
import pandas as pd
from bs4            import BeautifulSoup
from pprint         import pprint

# Uses regex to extract IDs from MP urls
# -- e.g. 'https://www.mountainproject.com/route/105884815/moby-grape/' outputs '105884815'

def get_id(url):
    id = ''

    # Regex find ID
    match = re.search(r'\/(area|route)\/(\d+)', url)

    # Check valid match
    if match:
        # Extract the ID number from the first capturing group
        id = match.group(2)

    # Invalid match
    else:
        raise Exception('Unable to locate route/area ID in url - {url}')
    
    return id

def get_directory():
    # Make request to get the route guide page
    url     = 'https://www.mountainproject.com/route-guide'
    content = requests.get(url).content
    soup    = BeautifulSoup(content, features = 'html.parser')
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

# Gets an area from MP given its ID
def get_area(id):
    url     = f'https://www.mountainproject.com/api/v2/areas/{id}'
    data = requests.get(url).json()
    return data

# Gets a route from MP given its ID
def get_route(id):
    url     = f'https://www.mountainproject.com/api/v2/routes/{id}'
    data    = requests.get(url).json()
    return data

# Gets the comments of a route or area from MP given its ID
def get_comments(id, type = 'Route'):
    # Make request to get the route guide page comments page
    url_format  = f'https://www.mountainproject.com/comments/forObject/Climb-Lib-Models-{type}/'
    url_query   = '?sortOrder=oldest&showAll=true'
    content     = requests.get(url_format + id + url_query).content
    soup        = BeautifulSoup(content, 'html.parser')

    # Create a list to store comments
    comments = []

    # Extract all comment IDs from HTML 
    comment_ids = re.findall(r"Comment-(\d+)", str(soup))
    comment_ids = set(comment_ids)

    for t_id in comment_ids:
        raw_comment     = soup.find(id= "Comment-" + t_id)
        comment_text    = soup.find_all(id= t_id + "-full")[0].text
        comment_time    = raw_comment.find_all(class_ = "comment-time")[0].text
        raw_user        = raw_comment.find(class_ = 'bio').find('a')
        user_name       = raw_user.text
        raw_user_id     = raw_user['href'].split('/')[-2]

        comments.append({
            'id': t_id,
            'text': comment_text.strip(), 
            'time': pd.to_datetime(dateparser.parse(comment_time)),
            'user': { 'name': user_name, 'id': raw_user_id }
        })

    return comments

def get_routes_in(area_id, route_list, only_ids = True):
    area = get_area(area_id)

    for child in area['children']:
        child_id = str(child['id'])

        if child['type'] == 'Route':
            if only_ids:
                route_list.append(child_id)
            else:
                route = get_route(child_id)
                route['comments'] = get_comments(child_id)
                route_list.append(route)
        else:
            get_routes_in(child_id, route_list, only_ids)

# DANGER: this function might take a couple billion years to run
def get_all_routes_ids():
    directory = get_directory()
    del directory['International']

    route_list = []

    for state in directory:
        area_id = get_id(directory[state])
        get_routes_in(area_id, route_list)

    return route_list