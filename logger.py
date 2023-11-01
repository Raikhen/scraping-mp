from config import log_values
from pprint import pprint

def lprint(str):
    if (log_values):
        print(str)

def lpprint(str):
    if (log_values):
        pprint(str)