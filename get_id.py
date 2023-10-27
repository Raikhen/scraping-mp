import re

# Uses regex to extract IDs from MP urls
# -- e.g. 'https://www.mountainproject.com/route/105884815/moby-grape/' outputs '105884815'

def get_id(url):
    id = ''

    #Regex find ID
    match = re.search(r"/route/(\d+)/", url)

    #Check valid match
    if match:
        # Extract the ID number from the first capturing group
        id = match.group(1)

    #Invalid match
    else:
        raise Exception('Unable to locate route ID in url - {url}')
    return id
