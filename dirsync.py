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
    # Sync file doesn't exist so its created and populated with data
    if (not os.path.exists(path)):
        with open (path, 'w') as f:
            for filename in os.listdir(directory):
                path = os.path.join(directory, filename)
                # Check if its a file
                if os.path.isfile(path) and filename != '.sync.json':
                    json_data[filename] = [[modified_time(path), gen_hash(path)]]
            f.write(json.dumps(json_data))
    else:
        # Sync file exists and we have to update its contents
        # Load json file
        try:
            with open (path) as json_file:
                data = json.load(json_file)
        except json.JSONDecodeError:
            data = {}
        
        with open (path, 'w+') as f:

            # Json file is empty
            if data == {}:
                for filename in os.listdir(directory):
                    path = os.path.join(directory, filename)
                    # Check if its a file
                    if os.path.isfile(path) and filename != '.sync.json':
                        data[filename] = [[modified_time(path), gen_hash(path)]]
                f.write(json.dumps(data))
            else: # Json file is not empty so contents can be updated
                for filename in os.listdir(directory):
                    path = os.path.join(directory, filename)

                    # Check if its a file
                    if os.path.isfile(path) and filename != '.sync.json':   
                        latest_modified_time = data[filename][0][0]
                        latest_hash = data[filename][0][1]

                        # Check if file has been modified
                        if (gen_hash(path) != latest_hash or modified_time(path) != latest_modified_time):
                            data[filename].insert(0, [modified_time(path), gen_hash(path)])
            
                # Write new sync data to json file
                f.write(json.dumps(data))

            

if __name__ == '__main__':
    directory = 'dir1'
    modify_sync_file(directory)
    
            