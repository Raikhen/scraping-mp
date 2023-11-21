import pandas               as      pd
from utils.db_utils         import  get_db
from utils.grade_utils      import  grade_dict
from random                 import  shuffle
from pprint                 import  pprint
from itertools              import  groupby
from utils.logger           import  lprint, lpprint
from elosports.elo          import Elo

db  = get_db()
MAX = 5000
match_threshold = 100

def filter_routes(route_with_ticks):
    route   = db['routes'].find_one({ '_id': route_with_ticks['_id'] })
    res     = True

    # Single-pitch climbs only
    res = res and route['pitches'] < 2

    # Only Sport, Trad, and TR routes
    res = res and 'Boulder' not in route['types']
    res = res and 'Aid' not in route['types']
    res = res and 'Ice' not in route['types']
    res = res and 'Mixed' not in route['types']
    res = res and 'Snow' not in route['types']

    # Only routes with a registered difficulty
    res = res and route['difficulty'] != ''

    return res

def group_by_route(ticks):
    ticked_routes_dict = {}

    for tick in ticks:
        if tick['route_id'] in ticked_routes_dict:
            ticked_routes_dict[tick['route_id']].append(tick)
        else:
            ticked_routes_dict[tick['route_id']] = [tick]

    ticked_routes = []

    for route_id in ticked_routes_dict:
        ticked_routes.append({
            '_id': route_id,
            'ticks': ticked_routes_dict[route_id]
        })

    return ticked_routes

def get_score(route):
    styles      = [tick['style'] for tick in route['ticks']]
    lead_styles = [tick['leadStyle'] for tick in route['ticks']]
    
    if 'Solo' in styles:
        return 0
    elif 'Onsight' in lead_styles:
        return 1
    elif 'Flash' in lead_styles:
        return 2
    elif 'Redpoint' in lead_styles or 'Pinkpoint' in lead_styles:
        return 3
    elif 'TR' in styles or 'Follow' in styles or 'Fell/Hung' in lead_styles:
        return 5
    else:
        return 4

def get_ticked_routes(user_id):
    # Get all of the user's ticks
    user_ticks      = db['ticks'].find({ 'user.id': user_id })
    user_ticks_list = list(user_ticks)

    # Group ticks by route and filter out boulder problems and multi-pitch routes
    user_routes     = []
    all_user_routes = group_by_route(user_ticks_list)

    # Filter routes and score each of them
    for route in all_user_routes:
        if filter_routes(route):
            user_routes.append({
                '_id': route['_id'],
                'score': get_score(route)
            })
    
    return user_routes

def generate_matches():
    matches = []

    lprint('Getting all the users ids')

    # Get all of the users ids
    user_ids = db['ticks'].distinct('user.id')
    user_ids.remove(200056064) # Ignore MP Testing Test

    lprint(f'Got {len(user_ids)} user ids')

    # Add a match for every pair of routes that someone has ticked
    for idx, user_id in enumerate(user_ids):
        print(f'Generating matches for user {user_id} ({idx + 1}/{len(user_ids)})')

        # Get all of the routes that the user has ticked
        lprint(f'Getting routes for user {user_id}')
        user_routes = get_ticked_routes(user_id)
        lprint(f'Got {len(user_routes)} routes for user {user_id}')
        
        for route1 in user_routes:
            for route2 in user_routes:
                if route1['_id'] != route2['_id']:
                    matches.append({
                        'user_id': user_id,
                        'route1': route1,
                        'route2': route2
                    })

        lprint(f'Added all the matches for user {user_id}')

    # Randomize the order of the matches
    shuffle(matches)

    # Return the matches
    return matches

def run_matches(matches):
    # Initialize the league
    routeLeague = Elo(k = 20)

    # All the routes that play at least one match
    route_ids = list(set(
        [m['route1']['_id'] for m in matches] +
        [m['route2']['_id'] for m in matches]
    ))

    match_counter = {}

    # Add all of those routes to the league
    for route_id in route_ids:
        routeLeague.addPlayer(route_id)
        match_counter[route_id] = 0

    lprint('Added all routes to the league')

    for match in matches:
        route1 = match['route1']
        route2 = match['route2']
        
        if route1['score'] > route1['score']:
            winner = route1['_id']
            loser = route2['_id']
        else:
            winner = route2['_id']
            loser = route1['_id']

        match_counter[route1['_id']] += 1
        match_counter[route2['_id']] += 1
        routeLeague.gameOver(winner, loser, 0)
    
    data = list(db['routes'].find(
        { '_id': { '$in': route_ids} },
        { '_id': 1, 'difficulty': 1, 'types': 1 }
    ))

    def filter_func(e):
        res = e['difficulty'] == 'Easy 5th' or e['difficulty'][0] in ['3', '4', '5']
        res = res and match_counter[e['_id']] >= match_threshold

        return res

    data = list(filter(filter_func, data))

    for e in data:
        # Add the elo rating to the route
        e['elo'] = routeLeague.ratingDict[e['_id']]

        # Add the numerical difficulty to the route
        difficulty              = e['difficulty'].split(' ')[0]
        difficulty              = difficulty if difficulty != 'Easy' else 'Easy 5th'
        e['number_difficulty']  = grade_dict[difficulty]

    df = pd.DataFrame.from_dict(data)
    lprint(df)
    lprint(df['number_difficulty'].corr(df['elo']))

# Run code
matches = generate_matches()
run_matches(matches)

