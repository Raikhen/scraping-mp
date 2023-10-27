import requests
import re
import pandas as pd
from pprint import pprint
from bs4    import BeautifulSoup
from get_id import get_id

example_url     = 'https://www.mountainproject.com/route/105884815/moby-grape/'

def scrape_comments(url):
    #Make request to get the route guide page comments page

    url_format = 'https://www.mountainproject.com/comments/forObject/Climb-Lib-Models-Route/'
    url_query = '?sortOrder=oldest&showAll=true'
    content = requests.get(url_format + get_id(url) + url_query).content
    soup    = BeautifulSoup(content, 'html.parser')

    #Create a list to store comments
    comments = []

    #Extract all comment IDs from HTML 
    comment_ids = re.findall(r"Comment-(\d+)", str(soup))
    comment_ids = set(comment_ids)

    for t_id in comment_ids:
        comment_text = soup.find_all(id= t_id + "-full")[0].text
        comment_time = soup.find_all(id= "Comment-" + t_id)[0].find_all(class_="comment-time")[0].text

        comments.append({
            'id': t_id,
            'text': comment_text.strip(), 
            'time': pd.to_datetime(comment_time)
        })

        break

    return comments

print(scrape_comments(example_url))