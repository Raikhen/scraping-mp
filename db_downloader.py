import json
from get_db import  get_db

def download_db():
    db      = get_db()
    json_db = {}

    # All the collections to be downloaded
    collections = ['users', 'ticks', 'areas', 'routes', 'comments']

    # Download each collection
    for c in collections:
        print(f'Downloading {c}')
        json_db[c] = list(db[c].find())
        print(f'Downloaded {c}')

    # Save json_db to file
    with open('db.json', 'w') as f:
        json.dump(json_db, f)