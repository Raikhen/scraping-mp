import re
import json
import time
import zlib
import requests
import dateparser
import pandas       as pd
from utils.logger   import lprint, lpprint
from bs4            import BeautifulSoup
from pprint         import pprint

MAX_PAGES = 1000

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
    try:
        data = requests.get(url).json()
    except:
        lprint("Too many requests... Retrying")
        time.sleep(3)
        return get_area(id)
    return data

def get_ticks_page(route_id, page_num=1):
    url = f'https://www.mountainproject.com/api/v2/routes/{str(route_id)}/ticks?page={str(page_num)}'

    try:
        return requests.get(url).json()
    except:
        lprint("Too many requests... Retrying")
        time.sleep(3)
        return get_ticks_page(route_id, page_num)

def get_ticks(route_id, start_page=1):
    done    = False
    data    = []
    i       = start_page

    while (not done) and (i <= MAX_PAGES):
        response = get_ticks_page(route_id, i)
        data += response['data']
        
        done = (response['next_page_url'] == None)
        i += 1

    return data

# Gets a route from MP given its ID
def get_route(id):
    url     = f'https://www.mountainproject.com/api/v2/routes/{id}'
    try: 
        data    = requests.get(url).json()
    except:
        lprint("Too many requests... Retrying")
        time.sleep(3)
        return get_route(id)
    return data

# Gets the comments of a route or area from MP given its ID
def get_comments(id):
    # Make request to get the route guide page comments page
    url_format  = f'https://www.mountainproject.com/comments/forObject/Climb-Lib-Models-Route/'
    url_query   = '?sortOrder=oldest&showAll=true'
    try: 
        content     = requests.get(url_format + str(id) + url_query).content
    except:
        lprint("Too many requests... Retrying")
        time.sleep(3)
        content = get_comments(id, type)

    comments = []
    try: 
        try: 
            soup        = BeautifulSoup(content, 'html.parser')
            # Create a list to store comment

            # Extract all comment IDs from HTML 
            comment_ids = re.findall(r"Comment-(\d+)", str(soup))
            comment_ids = set(comment_ids)

            for t_id in comment_ids:
                raw_comment     = soup.find(id= "Comment-" + t_id)
                if raw_comment is None:
                    continue
                comment_text    = soup.find_all(id= t_id + "-full")[0].text
                comment_time    = raw_comment.find_all(class_ = "comment-time")[0].text
                raw_user        = raw_comment.find(class_ = 'bio').find('a')
                if (raw_user is None):
                    #User is anonymous, create a unique ID for this user so that we can index it from 
                    #users database if need be
                    user_name = "Anonymous" + str(zlib.crc32(raw_comment.encode()))
                    raw_user_id     = zlib.crc32(raw_comment.encode())
                    lprint(f'User was anonymous, assigning ID: ' + str(zlib.crc32(raw_comment.encode())))
                else: 
                    user_name       = raw_user.text
                    raw_user_id     = int(raw_user['href'].split('/')[-2])
                

                comments.append({
                    'id': int(t_id),
                    'text': comment_text.strip(), 
                    'time': pd.to_datetime(dateparser.parse(comment_time)),
                    'user': { 'name': user_name, 'id': raw_user_id }
                })
        except: 
            lprint("HTML Parser failed, trying lxml...")
            soup        = BeautifulSoup(content, 'lxml')

            # Extract all comment IDs from HTML 
            comment_ids = re.findall(r"Comment-(\d+)", str(soup))
            comment_ids = set(comment_ids)

            for t_id in comment_ids:
                raw_comment     = soup.find(id= "Comment-" + t_id)
                if raw_comment is None:
                    continue
                comment_text    = soup.find_all(id= t_id + "-full")[0].text
                comment_time    = raw_comment.find_all(class_ = "comment-time")[0].text
                raw_user        = raw_comment.find(class_ = 'bio').find('a')
                if (raw_user is None):
                    #User is anonymous, create a unique ID for this user so that we can index it from 
                    #users database if need be
                    user_name = "Anonymous" + str(zlib.crc32(raw_comment.encode()))
                    raw_user_id     = zlib.crc32(raw_comment.encode())
                    lprint(f'User was anonymous, assigning ID: ' + str(zlib.crc32(raw_comment.encode())))
                else: 
                    user_name       = raw_user.text
                    raw_user_id     = int(raw_user['href'].split('/')[-2])
                

                comments.append({
                    'id': int(t_id),
                    'text': comment_text.strip(), 
                    'time': pd.to_datetime(dateparser.parse(comment_time)),
                    'user': { 'name': user_name, 'id': raw_user_id }
                })
    except Exception as e: 
        lprint("Comment parsing failed:")
        lprint(e)
        raise Exception()
        return comments


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