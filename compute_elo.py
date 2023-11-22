import pymongo
import pandas as pd
from random                 import  shuffle
from utils.db_utils         import  get_db
from utils.grade_utils      import  grade_dict
from utils.logger           import  lprint, lpprint

# Params
K                   = 1
BASE                = 2000
MIN_ROUTES_PER_USER = 10
MIN_USERS           = 50
MAX_USERS           = 10000

# Connect to the database
db = get_db()

def get_score(user_ticks):
    styles      = [tick['style'] for tick in user_ticks]
    lead_styles = [tick['leadStyle'] for tick in user_ticks]
    
    if 'Solo' in styles:
        return 0
    elif 'Onsight' in lead_styles:
        return 1
    elif 'Flash' in lead_styles:
        return 2
    elif 'Redpoint' in lead_styles or 'Pinkpoint' in lead_styles:
        return 3
    elif 'Fell/Hung' in lead_styles:
        return 4
    else:
        return -1

def scores_diff(s1, s2):
    return (s1 - s2 + 4) / 8

def update_ratings(user_ticks, valid_routes, ratings, counter):
    # Extract all routes ticked by the user
    user_ticked_routes = set()
    for tick in user_ticks:
        user_ticked_routes.add(tick['route_id'])

    # Filter invalid routes
    user_ticked_routes.intersection_update(valid_routes)

    # Compute scores and set initial ratings if necessary
    scores = {}
    for route in user_ticked_routes:
        route_ticks     = list(filter(lambda t: t['route_id'] == route, user_ticks))
        scores[route]   = get_score(route_ticks)

        if scores[route] != -1:
            # Set initial rating
            if route not in ratings:
                ratings[route] = BASE
            
            # Update counter
            if len(user_ticked_routes) >= MIN_ROUTES_PER_USER:
                if route not in counter:
                    counter[route] = 1
                else:
                    counter[route] += 1

    # Function to calculate the expected probability of winning
    def expected_result(rating_a, rating_b):
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    # Update ratings
    for route1 in user_ticked_routes:
        for route2 in user_ticked_routes:
            # Skip update if the routes are the same
            if route1 == route2:
                continue

            # Skip update if one of the routes has no score
            if -1 in [scores[route1], scores[route2]]:
                continue

            # Get the result of the match
            result = scores_diff(scores[route1], scores[route2])

            # Calculate expected probability of winning
            expected_a = expected_result(ratings[route1], ratings[route1])
            expected_b = expected_result(ratings[route2], ratings[route2])

            # Update ratings based on outcome
            ratings[route1] += K * (result - expected_a)
            ratings[route2] += K * (1 - result - expected_b)

    return ratings

def run_matches():
    ticks_col = db['ticks']
    routes_col = db['routes']

    tick_pipeline = [
        {
            '$match': {
                '$or': [
                    {'style': 'Solo'},
                    {'leadStyle': {'$ne': ''}}
                ]
            }
        },
        {
            '$group': 
            {
                '_id': '$user.id', 
                'ticks': {'$push': {
                        '_id': '$_id',
                        'route_id': '$route_id',
                        'style': '$style',
                        'leadStyle': '$leadStyle'
                    }}
            }
        }
    ]

    route_pipeline = [
        {
            '$match': {
                '$expr': {
                    '$and': [
                        { '$lt': ['$pitches', 2] },  # Single-pitch climbs only
                        {
                            '$not': {
                                '$in': ['$types', ['Boulder', 'Aid', 'Ice', 'Mixed', 'Snow']]
                            }
                        },  # Only Sport, Trad, and TR routes
                        { '$ne': ['$difficulty', ''] },  # Only routes with a registered difficulty
                        { '$ne': ['$parent_id', '112166257'] }  # No generic routes
                    ]
                }
            }
        }
    ]

    def f(route):
        s = set(['Boulder', 'Aid', 'Ice', 'Mixed', 'Snow'])
        return not set(route['types']).intersection(s)

    # Get all valid routes and ticks
    ticks_grouped_by_user   = list(ticks_col.aggregate(tick_pipeline))
    valid_routes            = list(routes_col.aggregate(route_pipeline))
    valid_routes            = list(filter(f, valid_routes))    
    valid_route_ids         = [route['_id'] for route in valid_routes]

    # Initialize ratings
    ratings = {}
    counter = {}

    # Shuffle the users, only makes sense when MAX_USERS is small
    shuffle(ticks_grouped_by_user)

    # Update ratings for each user
    for i, user_ticks in enumerate(ticks_grouped_by_user[:MAX_USERS]):
        # lprint(f'Processing user {i + 1} of {len(ticks_grouped_by_user)}')
        update_ratings(user_ticks['ticks'], valid_route_ids, ratings, counter)

    data = []

    for route in valid_routes:
        if route['_id'] in ratings.keys() and route['_id'] in counter:
            if counter[route['_id']] >= MIN_USERS:
                # Add the elo rating to the route
                route['elo_rating'] = ratings[route['_id']]

                # Add the numerical difficulty to the route
                difficulty  = route['difficulty'].split(' ')[0]
                difficulty  = difficulty if difficulty != 'Easy' else 'Easy 5th'

                # We need to check because there are some routes with only safety grades
                if difficulty in grade_dict:
                    route['difficulty_num'] = grade_dict[difficulty]

                    # Add to data for dataframe
                    keys = ['_id', 'difficulty', 'difficulty_num', 'elo_rating', 'types']
                    data.append({ key: route[key] for key in keys })

    # Make dataframe
    df = pd.DataFrame.from_dict(data)
    df = df.set_index('_id')

    # And return it
    return df

def update_db():
    df = run_matches()

    update_operations = []

    for index, row in df.iterrows():
        update_operations.append(
            pymongo.UpdateOne(
                { '_id': index },
                { '$set': { 'elo_rating': row['elo_rating'] } }
            )
        )

    result = db['routes'].bulk_write(update_operations)