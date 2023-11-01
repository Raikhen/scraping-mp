from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from urllib.parse import quote_plus
from scrape import get_route, get_area, get_id, get_directory
from logger import lprint, lpprint

logger = True

username = quote_plus('EvilMonkey')
password = quote_plus('&a@JREztYS5@EyPL')
cluster = '<clusterName>'
authSource = '<authSource>'
authMechanism = '<authMechanism>'
uri = 'mongodb+srv://' + username + ':' + password + '@cluster0.rhyjndk.mongodb.net/?retryWrites=true&w=majority'

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    lprint("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    lprint(e)

db = client["mountain_project"]

def populate_routes_in(areas, routes, area_id):
    area = get_area(area_id)
    for child in area['children']:

        child_id = str(child['id'])

        if child['type'] == 'Route':

            new_route = {
                "_id": child_id,
                "area_id": area_id
            }

            route_exists = routes.find_one({"_id": child_id})

            if route_exists is None:
                # Object doesn't exist, so add it to the collection
                result = routes.insert_one(new_route)
                lprint("New route added with _id: " + result.inserted_id)
            else:
                # Object with the same name already exists; you can update it or take other action
                lprint(f"Route {child_id} already exists.")

        else:

            new_area = {
                "_id": child_id, 
                "parent_id": area_id
            }
        
            area_exists = areas.find_one({"_id": child_id})

            if area_exists is None:
                # Object doesn't exist, so add it to the collection
                result = areas.insert_one(new_area)
                lprint("New area added with _id: " + result.inserted_id)
            else:
                # Object with the same name already exists; you can update it or take other action
                lprint(f"Area {area_id} already exists.")
                
            populate_routes_in(areas, routes, child_id)

def populate_routes(db):
    areas = db['areas']
    routes = db['routes']
    directory = get_directory()
    del directory['International']

    for state in directory:
        area_id = get_id(directory[state])

        new_area = {
            "_id": area_id, 
            "parent_id": None
        }

        area_exists = areas.find_one({"_id": area_id})

        if area_exists is None:
            # Object doesn't exist, so add it to the collection
            result = areas.insert_one(new_area)
            lprint("New area added with _id:", result.inserted_id)
        else:
            # Object with the same name already exists; you can update it or take other action
            lprint(f"Area {area_id} already exists.")

        populate_routes_in(areas, routes, area_id)
        break

populate_routes(db)