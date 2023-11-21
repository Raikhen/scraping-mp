from utils.db_utils         import  get_db
from utils.grade_utils      import  grade_dict
from utils.logger           import  lprint, lpprint

db = get_db()

def update_ranks(user_ticks, valid_routes):

    #Extract all routes ticked by the user
    user_ticked_routes = set()
    for tick in user_ticks:
        user_ticked_routes.add(tick['route_id'])


    #Filter invalid routes
    for route in user_ticked_routes:
        if route not in valid_routes:
            user_ticked_routes.remove(route)

    #Score routes
    scores = {}
    for route in user_ticked_routes:
        score = 0
        score_entry = {'route': route, 'score': score}
        scores.append(score_entry)
    #Update ranking

    lpprint(scores)
    return

def run_matches():
    ticks_col = db['ticks']
    routes_col = db['routes']

    tick_pipeline = [
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
                        {'$lt': ['$pitches', 2]},  # Single-pitch climbs only
                        {
                            '$not': {
                                '$in': [['$types'], ['Boulder', 'Aid', 'Ice', 'Mixed', 'Snow']]
                            }
                        },  # Only Sport, Trad, and TR routes
                        {'$ne': ['$difficulty', '']}  # Only routes with a registered difficulty
                    ]
                }
            }
        }
    ]

    lprint("Aggregating data...")
    tick_grouped_by_user = list(ticks_col.aggregate(tick_pipeline))
    valid_routes = list(routes_col.aggregate(route_pipeline))
    lprint("Data succesfully aggregated!")

    for user_ticks in tick_grouped_by_user:
        update_ranks(user_ticks['ticks'], valid_routes)
        break

run_matches()