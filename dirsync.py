import hashlib
import os
import datetime
from time import gmtime, strftime
import json

def gen_hash(path):
    """
    Function to generate a sha-256 hash for a file

    Parameters:
        path : path to the file
    
    Returns:
        hexadecimal : sha-256 hash 
    """
    sha256_hash = hashlib.sha256()
    with open (path, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b''):
            sha256_hash.update(byte_block) 
    return sha256_hash.hexdigest()

def modified_time(path):
    """
    Function to get the last modified time of a file

    Parameters:
        path : path to the file
    
    Returns:
        string : last modifed time
    """
    time = os.path.getmtime(path)
    date = datetime.datetime.fromtimestamp(int(time)).strftime('%Y-%m-%d %H:%M:%S')
    timezone = strftime('%z', gmtime())
    return str(date) + " " + str(timezone)

def modify_sync_file(directory):
    """
    Function to create a sync file if it doesn't exist

    Parameters:
        directory : path to the directory
    """
    path = os.path.join(directory, '.sync.json')
    json_data = {}

    # Check if .sync file exists
    if (not os.path.exists(path)):
        with open (path, 'w') as f:
            for filename in os.listdir(directory):
                path = os.path.join(directory, filename)
                # Check if its a file
                if os.path.isfile(path) and filename != '.sync.json':
                    json_data[filename] = [[modified_time(path), gen_hash(path)]]
            f.write(json.dumps(json_data))
    else:
        pass

if __name__ == '__main__':
    directory = 'dir1'
    modify_sync_file(directory)
    
            