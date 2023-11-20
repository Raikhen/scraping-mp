import json
from logger                 import  lprint, lpprint
from pymongo.mongo_client   import  MongoClient
from pymongo.server_api     import  ServerApi
from urllib.parse           import  quote_plus

def get_db():
    # Connect to Mongo Server in Trust Lab
    username = quote_plus('EvilMonkey')
    password = quote_plus('&a@JREztYS5@EyPL')
    uri = f'mongodb://{username}:{password}@10.28.54.198:27017/?retryWrites=true&w=majority'

    # Create a new client and connect to the server
    client = MongoClient(uri, server_api = ServerApi('1'))

    # Send a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        lprint("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        lprint(e)

    return client["mountain_project"]

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