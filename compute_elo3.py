from utils.db_utils         import  get_db
from utils.grade_utils      import  grade_dict
from utils.logger           import  lprint, lpprint

db = get_db()

def get_all_routes():
    db['routes'].find(
        { 'difficulty': { '$ne': '' },  },
        {  }
    )
