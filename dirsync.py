import hashlib
import os, sys
import datetime
from time import gmtime, strftime, ctime
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
    date = datetime.datetime.fromtimestamp(int(time))
    timezone = str(date - datetime.datetime.utcfromtimestamp(int(time)))
    if '-' in timezone:
        timezone = '-' + timezone[8:10] + timezone[11:13]
    else:
        timezone = '+' + timezone[0:2] + timezone[3:5]
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
                if os.path.isfile(path) and filename[0] != '.':
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
                    if os.path.isfile(path) and filename[0] != '.':
                        data[filename] = [[modified_time(path), gen_hash(path)]]
                f.write(json.dumps(data))
            else: # Json file is not empty so contents can be updated
                for filename in os.listdir(directory):
                    path = os.path.join(directory, filename)

                    # Check if its a file
                    if os.path.isfile(path) and filename[0] != '.':   
                        latest_modified_time = data[filename][0][0]
                        latest_hash = data[filename][0][1]

                        # Check if file has been modified
                        if (gen_hash(path) != latest_hash or modified_time(path) != latest_modified_time):
                            data[filename].insert(0, [modified_time(path), gen_hash(path)])
            
                # Write new sync data to json file
                f.write(json.dumps(data))

def sync(dir1, dir2):

    modify_sync_file(dir1)
    modify_sync_file(dir2)

    # load json data for dir1
    try:
        with open (os.path.join(dir1, '.sync.json')) as json_file:
            dir1_data = json.load(json_file)
    except json.JSONDecodeError:
        dir1_data = {}

    #load json data for dir2
    try:
        with open (os.path.join(dir2, '.sync.json')) as json_file:
            dir2_data = json.load(json_file)
    except json.JSONDecodeError:
        dir2_data = {}

    print(dir1_data)
    print(dir2_data)
    for file1 in os.listdir(dir1):
        for file2 in os.listdir(dir2):
            if (file1 == file2):
                pass

                  

if __name__ == '__main__':
    dir1 = sys.argv[1]
    dir2 = sys.argv[2]
    #sync("dir1", "dir2")
    sync(dir1, dir2)

    
            