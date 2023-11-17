from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from urllib.parse import quote_plus
from scrape import get_route, get_area, get_id, get_directory, get_comments
from logger import lprint, lpprint
from resume import find_root_parent_id
from multiprocessing.pool import ThreadPool as Pool
from multiprocessing import cpu_count
from joblib import Parallel, delayed
from tqdm import tqdm

#Connect to Mongo Server in Trust Lab
username = quote_plus('EvilMonkey')
password = quote_plus('&a@JREztYS5@EyPL')
uri = 'mongodb://' + username + ':' + password + '@10.28.54.198:27017/?retryWrites=true&w=majority'

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
    area_exists = areas.find_one({"_id": int(area_id)})
    area = get_area(area_id)
    area_processed = process_area(area)
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

            route_exists = routes.find_one({"_id": int(child_id)})

            if route_exists is None:
                # Object doesn't exist, so add it to the collection
                route = get_route(child_id)
                route = process_route(route)
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

def populate_comments(db, start_route=105714687):
    #Gather collections
    users_col = db['users']
    comments_col = db['comments']

    #Get route ids
    json_route_ids = db['routes'].find({"_id": {"$exists": True}}, {"_id": 1})
    route_ids = sorted([json["_id"] for json in json_route_ids])
    start_idx = route_ids.index(start_route)

    #Track comments seen for progress bar
    total_comments_seen = db['comments'].count_documents({})
    total_routes_seen = start_idx

    with tqdm(total=int(len(route_ids)*(total_comments_seen/total_routes_seen)), colour='green') as pbar:
        pbar.update(total_comments_seen)

        try:
            for i in range(start_idx, len(route_ids)):
                total_routes_seen += 1

                comments = get_comments(route_ids[i])
                for comment in comments:

                    total_comments_seen += 1
                    pbar.update(1)

                    #Add user to database
                    user = comment['user']
                    user = process_user(user)
                    user_id = user['_id']
                    user_exists = users_col.find_one({"_id": user_id})
                    if user_exists is None:
                        # Object doesn't exist, so add it to the collection
                        result = users_col.insert_one(user)
                        lprint("New user added with id: " + str(result.inserted_id))
                    else:
                        # Object with the same name already exists; you can update it or take other action
                        lprint(f"User {user_id} already exists.")

                    #Add comment to database
                    comment = process_comment(comment)
                    comment['route_id'] = route_ids[i]
                    comment_id = comment['_id']
                    comment_exists = comments_col.find_one({"_id": comment_id})
                    if comment_exists is None:
                        # Object doesn't exist, so add it to the collection
                        result = comments_col.insert_one(comment)
                        lprint(f"New comment added for route {route_ids[i]} with id: " + str(result.inserted_id))
            
                    else:
                        # Object with the same name already exists; you can update it or take other action
                        lprint(f"Comment {comment_id} already exists.")

                pbar.total = int(len(route_ids)*(total_comments_seen/total_routes_seen))
                pbar.refresh()

        except Exception as e:
            lprint("Broke on Route ID - " + str(route_ids[i]))
            lprint("Last Known Total Comments was - " + str(int(len(route_ids)*(total_comments_seen/total_routes_seen))))


def directory_index(directory, area_id):
    index = None
    for i, state in enumerate(directory):
        if get_id(directory[state]) == area_id:
            index = i
    return index

# def worker(state, db, start_id, areas, routes, directory, worker_id):
#     area_id = get_id(directory[state])
#     if directory_index(directory, area_id) >= directory_index(directory, find_root_parent_id(db, start_id)):
#         populate_routes_in(areas, routes, area_id, worker_id)

# def parallel_populate_routes(db, start_id=105905173):
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

def process_comment(comment):
    comment_copy = comment.copy()
    comment_copy['_id'] = comment_copy.pop('id')
    comment_copy['user_id'] = comment_copy['user'].pop('id')
    comment_copy.pop('user')
    return comment_copy

def process_user(user):
    user = user.copy()
    user['_id'] = user.pop('id')
    return user

populate_comments(db, start_route=112506685)