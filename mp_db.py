from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from urllib.parse import quote_plus
from scrape import get_route, get_area, get_id, get_directory

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
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client["mountain_project"]

def populate_routes_in(areas, routes, area_id):
    area = get_area(area_id)

    for child in area['children']:
        child_id = str(child['id'])

        if child['type'] == 'Route':
            # Check if route exists
            id_str = str(child['id'])

            new_route = {
                "_id": ObjectId(id_str),
            }

            route_exists = routes.find_one({"_id": id_str})

            if route_exists is None:
                # Object doesn't exist, so add it to the collection
                result = routes.insert_one(new_route)
                print("New route added with _id:", result.inserted_id)
            else:
                # Object with the same name already exists; you can update it or take other action
                print("Route {id_str} already exists.")

        else:
            populate_routes_in(areas, routes, child_id)

def populate_routes(db):
    areas = db['areas']
    routes = db['routes']
    directory = get_directory()
    del directory['International']

    for state in directory:
        area_id = get_id(directory[state])
        populate_routes_in(area_id, areas, routes)
        break