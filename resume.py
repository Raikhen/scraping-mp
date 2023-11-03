from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from urllib.parse import quote_plus
from logger import lprint, lpprint

def find_root_parent_id(db, id_to_find, terminal_id=0):
    def find_recursive(current_id):
        document = db['areas'].find_one({'_id': current_id})
        if document is None:
            return None
        if document['parent']['id'] == terminal_id:
            return current_id
        return find_recursive(document['parent']['id'])

    root_parent_id = find_recursive(id_to_find)
    return str(root_parent_id)