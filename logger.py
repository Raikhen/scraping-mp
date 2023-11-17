from config import log_values, log_to_file, log_file, id_file, log_directory
from pprint import pprint
import sys
import os
import time
import hashlib
import random
import json

first_run_flag = True

def get_or_create_unique_id():
    global first_run_flag 

    if first_run_flag:
        # Ensure the 'logs' directory exists
        logs_directory = "logs"
        os.makedirs(log_directory, exist_ok=True)

        # Generate a new unique ID and save it to the file
        try:
            with open(id_file, 'r') as file:
                counter = int(json.load(file)["id"])
        except (FileNotFoundError, json.JSONDecodeError):
            counter = 0

        counter += 1
        with open(id_file, 'w') as file_write:
            json.dump({"id": counter}, file_write)

        unique_id = counter
        first_run_flag = False
    else: 
        # Read the existing unique ID from the file
        with open(id_file, 'r') as file:
            unique_id = json.load(file)["id"]

    return str(unique_id)


def lprint(str):
    if (log_values):
        if (not log_to_file):
            print(str)
        else:
            # Redirect stdout to a file temporarily
            file_name = log_file + get_or_create_unique_id() + ".log"
            with open(file_name, 'a') as outfile:
                sys.stdout = outfile
                print(str)
                sys.stdout = sys.__stdout__  # Reset stdout to its original value


def lpprint(str):
    if (log_values):
        if (not log_to_file):
            pprint(str)
        else:
            # Redirect stdout to a file temporarily
            file_name = log_file + get_or_create_unique_id() + ".log"
            with open(file_name, 'a') as outfile:
                sys.stdout = outfile
                pprint(str)
                sys.stdout = sys.__stdout__  # Reset stdout to its original value

