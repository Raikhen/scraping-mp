from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from urllib.parse import quote_plus
from scrape import get_route, get_area, get_id, get_directory
from logger import lprint, lpprint
from resume import find_root_parent_id
from multiprocessing.pool import ThreadPool as Pool
from multiprocessing import cpu_count
from joblib import Parallel, delayed

username = quote_plus('EvilMonkey')
password = quote_plus('&a@JREztYS5@EyPL')
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

def populate_routes_in(areas, routes, area_id, worker_id = -1):
    area = get_area(area_id)
    area_processed = process_area(area)

    area_exists = areas.find_one({"_id": int(area_id)})
    if area_exists is None:
        # Object doesn't exist, so add it to the collection
        result = areas.insert_one(area_processed)
        if (worker_id == -1):
            lprint("New area added with id: " + str(result.inserted_id))
        else: 
            lprint(f"[Worker {worker_id}] New area added with id: " + str(result.inserted_id))
    else:
        # Object with the same name already exists; you can update it or take other action
        if (worker_id == -1):
            lprint(f"Area {area_id} already exists.")
        else: 
            lprint(f"[Worker {worker_id}] Area {area_id} already exists.")

    for child in area['children']:

        child_id = str(child['id'])

        if child['type'] == 'Route':

            route = get_route(child_id)
            route = process_route(route)

            route_exists = routes.find_one({"_id": int(child_id)})

            if route_exists is None:
                # Object doesn't exist, so add it to the collection
                result = routes.insert_one(route)
                if (worker_id == -1):
                    lprint("New route added with id: " + str(result.inserted_id))
                else: 
                    lprint(f"[Worker {worker_id}] New route added with id: " + str(result.inserted_id))
            else:
                # Object with the same name already exists; you can update it or take other action
                if (worker_id == -1):
                    lprint(f"Route {child_id} already exists.")
                else: 
                    lprint(f"[Worker {worker_id}] Route {child_id} already exists.")

        else: 
            populate_routes_in(areas, routes, child_id, worker_id)

def populate_routes(db, start_id = 105905173):
    started = False
    areas = db['areas']
    routes = db['routes']
    directory = get_directory()
    del directory['International']
    for state in directory:
        area_id = get_id(directory[state])
        if (find_root_parent_id(db, start_id) == area_id):
            started = True
        if (started):
            populate_routes_in(areas, routes, area_id)

def directory_index(directory, area_id):
    index = None
    for i, state in enumerate(directory):
        if get_id(directory[state]) == area_id:
            index = i
    return index

def worker(state, db, start_id, areas, routes, directory, worker_id):
    area_id = get_id(directory[state])
    if directory_index(directory, area_id) >= directory_index(directory, find_root_parent_id(db, start_id)):
        populate_routes_in(areas, routes, area_id, worker_id)

def parallel_populate_routes(db, start_id=105905173):
    areas = db['areas']
    routes = db['routes']
    directory = get_directory()
    del directory['International']

    # Create a pool of worker processes
    pool = Pool(processes=cpu_count())  # Use the number of CPU cores available

    worker_ids = range(pool._processes)  # Generate worker identifiers

    # Use the pool of processes to parallelize the work
    # lprint([(worker_id, state) for worker_id, state in zip(, directory)])
    pool.starmap(worker, [(state, db, start_id, areas, routes, directory, worker_id) for worker_id, state in zip(list(worker_ids) * (len(directory) // len(worker_ids)), directory)])
    pool.close()
    pool.join()


    return

def process_area(area):
    area_copy = area.copy()
    del area_copy['children']
    area_copy['_id'] = area_copy.pop('id')
    return area_copy

def process_route(route):
    route_copy = route.copy()
    route_copy['_id'] = route_copy.pop('id')
    return route_copy

last_checked_area = 112559685
parallel_populate_routes(db, last_checked_area)