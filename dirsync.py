#!/usr/bin/env python3
from fileinput import filename
import hashlib
import os, sys, time
import datetime
from time import gmtime, strftime, ctime
import json
import shutil

def change_modification_time(path, date):
    """
    Changes the modification time for a file

    Parameters:
        path : path to the file
        date : datetime object 
    """
    mod_time = time.mktime(date.timetuple())
    os.utime(path, (mod_time, mod_time))

def date_to_datetime(date):
    """
    Changes date and time string to datetime object

    Parameters:
        date : date and time string
    
    Returns:
        datetime : datetime object 
    """
    return datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S %z')

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
    path = os.path.join(directory, '.sync')
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
            f.write(json.dumps(json_data, indent=4))
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
                f.write(json.dumps(data, indent=4))
            else: # Json file is not empty so contents can be updated
                for filename in os.listdir(directory):
                    path = os.path.join(directory, filename)

                    # Check if its a file
                    if os.path.isfile(path) and filename[0] != '.': 
                        try:  
                            latest_modified_time = data[filename][0][0]
                            latest_hash = data[filename][0][1]

                            # Check if file has been modified
                            if (gen_hash(path) != latest_hash and latest_hash != "deleted"):
                                data[filename].insert(0, [modified_time(path), gen_hash(path)])
                            
                            if (modified_time(path) != latest_modified_time and gen_hash(path) == latest_hash):
                                # Change modification time of the file
                                change_modification_time(path, date_to_datetime(latest_modified_time))
                        except Exception as e:
                            data[filename] = [[modified_time(path), gen_hash(path)]]

            
                # Write new sync data to json file
                f.write(json.dumps(data, indent=4))

def sync(dir1, dir2):
    """
    Function to sync the content of two directories

    Parameters:
        dir1 : string path to first directory
        dir2 : string path to second directory
    """

    modify_sync_file(dir1)
    modify_sync_file(dir2)

    # load json data for dir1
    try:
        with open (os.path.join(dir1, '.sync')) as json_file:
            dir1_data = json.load(json_file)
    except json.JSONDecodeError:
        dir1_data = {}

    #load json data for dir2
    try:
        with open (os.path.join(dir2, '.sync')) as json_file:
            dir2_data = json.load(json_file)
    except json.JSONDecodeError:
        dir2_data = {}

    for file1 in dir1_data:
        for file2 in dir2_data:
            if (file1 == file2): # Same file so we sync them

                if (dir1_data[file1][0][1] == "deleted" and dir2_data[file2][0][1] == "deleted"):
                    continue

                # If hash is the same and different modification times
                if (dir1_data[file1][0][1] == dir2_data[file2][0][1] and dir1_data[file1][0][0] != dir2_data[file2][0][0]):
                    date1 = datetime.datetime.strptime(dir1_data[file1][0][0], '%Y-%m-%d %H:%M:%S %z')
                    date2 = datetime.datetime.strptime(dir2_data[file2][0][0], '%Y-%m-%d %H:%M:%S %z')
                    
                    if date1 < date2:
                        # date1 is earlier so repleace date2 with date1
                        dir2_data[file2][0][0] = dir1_data[file1][0][0]
                        change_modification_time(os.path.join(dir2, file2), date1)
                    elif date2 < date1:
                        # date2 is earlier so replace date1 with date2
                        dir1_data[file1][0][0] = dir2_data[file2][0][0]
                        change_modification_time(os.path.join(dir1, file1), date2)
                    
                    # write new data to sync files
                    with open (os.path.join(dir1, '.sync'), 'w') as f:
                        f.write(json.dumps(dir1_data, indent=4))
                    with open (os.path.join(dir2, '.sync'), 'w') as f:
                        f.write(json.dumps(dir2_data, indent=4))
                else:
                    # Check for file 1 digest in list of file 2 digests
                    file1_hash = dir1_data[file1][0][1]
                    for file2_data in dir2_data[file2]:
                        if (file1_hash == file2_data[1] and file1_hash != dir2_data[file2][0][1]):
                            # Change dir1's sync file
                            dir1_data[file1].insert(0, dir2_data[file2][0])
                            with open (os.path.join(dir1, '.sync'), 'w') as f:
                                f.write(json.dumps(dir1_data, indent=4))

                            # Update file in dir1
                            shutil.copy2(os.path.join(dir2, file2), os.path.join(dir1, file1))
                            break


                    # Check for file 2 digest in list of file 1 digests
                    file2_hash = dir2_data[file2][0][1]
                    for file1_data in dir1_data[file1]:
                        if (file2_hash == file1_data[1] and file2_hash != dir1_data[file1][0][1]):
                            # Change dir2's sync file
                            dir2_data[file2].insert(0, dir1_data[file1][0])
                            with open (os.path.join(dir2, '.sync'), 'w') as f:
                                f.write(json.dumps(dir2_data, indent=4))
                            
                            # Update file in dir2
                            shutil.copy2(os.path.join(dir1, file1), os.path.join(dir2, file2))
                            break
                    
                    # Check if same files have unique digests in both dirs
                    unique_digest = True
                    for data1 in dir1_data[file1]:
                        for data2 in dir2_data[file2]:
                            if (data1[1] == data2[1]):
                                unique_digest = False
                    
                    if (unique_digest): # Keep file with latest modification time
                        if (date_to_datetime(dir1_data[file1][0][0]) < date_to_datetime(dir2_data[file2][0][0])):
                            # Change dir1's sync file
                            dir1_data[file1].insert(0, dir2_data[file2][0])
                            with open (os.path.join(dir1, '.sync'), 'w') as f:
                                f.write(json.dumps(dir1_data, indent=4))
                            
                            # Update file in dir1
                            shutil.copy2(os.path.join(dir2, file2), os.path.join(dir1, file1))
                        
                        elif (date_to_datetime(dir1_data[file1][0][0]) > date_to_datetime(dir2_data[file2][0][0])):
                            # Change dir2's sync file
                            dir2_data[file2].insert(0, dir1_data[file1][0])
                            with open (os.path.join(dir2, '.sync'), 'w') as f:
                                f.write(json.dumps(dir2_data, indent=4))
                            
                            # Update file in dir2
                            shutil.copy2(os.path.join(dir1, file1), os.path.join(dir2, file2))
    
    # Deletions

    # Check for if file was deleted then created again
    for del_file1 in os.listdir(dir1):
        try:
            if dir2_data[del_file1][0][1] == "deleted":
                # deleted file has been recreated in dir2
                shutil.copy2(os.path.join(dir1, del_file1), os.path.join(dir2, del_file1))

                dir1_data[del_file1].insert(0, [modified_time(os.path.join(dir1, del_file1)), gen_hash(os.path.join(dir1, del_file1))])
                dir2_data[del_file1].insert(0, [modified_time(os.path.join(dir2, del_file1)), gen_hash(os.path.join(dir2, del_file1))])

                with open (os.path.join(dir1, '.sync'), 'w') as f:
                    f.write(json.dumps(dir1_data, indent=4))
                
                with open (os.path.join(dir2, '.sync'), 'w') as f:
                    f.write(json.dumps(dir2_data, indent=4))
        except Exception as e:
            continue

    for del_file2 in os.listdir(dir2):
        try:
            if (dir1_data[del_file2][0][1] == "deleted"):
                shutil.copy2(os.path.join(dir2, del_file2), os.path.join(dir1, del_file2))

                dir1_data[del_file2].insert(0, [modified_time(os.path.join(dir1, del_file2)), gen_hash(os.path.join(dir1, del_file2))])
                dir2_data[del_file2].insert(0, [modified_time(os.path.join(dir2, del_file2)), gen_hash(os.path.join(dir2, del_file2))])

                with open (os.path.join(dir1, '.sync'), 'w') as f:
                    f.write(json.dumps(dir1_data, indent=4))
                
                with open (os.path.join(dir2, '.sync'), 'w') as f:
                    f.write(json.dumps(dir2_data, indent=4))
        except Exception as e:
            continue


    dir1_files = []
    dir2_files = []

    for f1 in os.listdir(dir1):
        if (not '.sync' in f1):
            dir1_files.append(f1)
    
    for f2 in os.listdir(dir2):
        if (not '.sync' in f2):
            dir2_files.append(f2)
    
    # Check if file has been deleted in dir1
    for del1 in dir1_data:
        if (del1 not in dir1_files and del1 in dir2_files):
            # File has been deleted in dir1
            datenow = datetime.datetime.now()
            utcnow = datetime.datetime.utcnow()
            datenow = datenow.replace(microsecond=0)
            utcnow = utcnow.replace(microsecond=0)
            timezone = str(datenow - utcnow)
            if '-' in timezone:
                timezone = '-' + timezone[8:10] + timezone[11:13]
            else:
                timezone = '+' + timezone[0:2] + timezone[3:5]
            
            dir1_data[del1].insert(0, [str(datenow) + " " + str(timezone) , "deleted"])
            dir2_data[del1].insert(0, [str(datenow) + " " + str(timezone) , "deleted"])

            with open (os.path.join(dir1, '.sync'), 'w') as f:
                f.write(json.dumps(dir1_data, indent=4))
            
            with open (os.path.join(dir2, '.sync'), 'w') as f:
                f.write(json.dumps(dir2_data, indent=4))
            # Delete file in dir2
            os.remove(os.path.join(dir2, del1))
    
    # Check if file is deletd in dir2
    for del2 in dir2_data:
        if (del2 not in dir2_files and del2 in dir1_files):
            # File has been deleted in dir2
            datenow = datetime.datetime.now()
            utcnow = datetime.datetime.utcnow()
            datenow = datenow.replace(microsecond=0)
            utcnow = utcnow.replace(microsecond=0)
            timezone = str(datenow - utcnow)
            if '-' in timezone:
                timezone = '-' + timezone[8:10] + timezone[11:13]
            else:
                timezone = '+' + timezone[0:2] + timezone[3:5]
            
            dir1_data[del2].insert(0, [str(datenow) + " " + str(timezone) , "deleted"])
            dir2_data[del2].insert(0, [str(datenow) + " " + str(timezone) , "deleted"])
            
            with open (os.path.join(dir1, '.sync'), 'w') as f:
                f.write(json.dumps(dir1_data, indent=4))
            
            with open (os.path.join(dir2, '.sync'), 'w') as f:
                f.write(json.dumps(dir2_data, indent=4))

            # Delete file in dir1
            os.remove(os.path.join(dir1, del2))

    # Sub directories
    for folder1 in os.listdir(dir1):
        for folder2 in os.listdir(dir2):
            if (folder1 == folder2 and os.path.isdir(os.path.join(dir1, folder1)) and os.path.isdir(os.path.join(dir2, folder2))):
                sync(os.path.join(dir1, folder1), os.path.join(dir2, folder2))
    
    # Sync non mutual files
    dir1_files = []
    dir2_files = []

    for f1 in os.listdir(dir1):
        if (not '.sync' in f1):
            dir1_files.append(f1)
    
    for f2 in os.listdir(dir2):
        if (not '.sync' in f2):
            dir2_files.append(f2)

    for f1_file in dir1_files:
        if (f1_file not in dir2_files):
            # If its a file we update the sync file
            if (os.path.isfile(os.path.join(dir1, f1_file))):
                shutil.copy2(os.path.join(dir1, f1_file), os.path.join(dir2, f1_file))
                dir2_data[f1_file] = dir1_data[f1_file]
                with open (os.path.join(dir2, '.sync'), 'w') as f:
                    f.write(json.dumps(dir2_data, indent=4))
            elif (os.path.isdir(os.path.join(dir1, f1_file))):
                shutil.copytree(os.path.join(dir1, f1_file), os.path.join(dir2, f1_file))
    
    for f2_file in dir2_files:
        if (f2_file not in dir1_files):
            # If its a file we update the sync file
            if (os.path.isfile(os.path.join(dir2, f2_file))):
                shutil.copy2(os.path.join(dir2, f2_file), os.path.join(dir1, f2_file))
                dir1_data[f2_file] = dir2_data[f2_file]
                with open (os.path.join(dir1, '.sync'), 'w') as f:
                    f.write(json.dumps(dir1_data, indent=4))
            elif (os.path.isdir(os.path.join(dir2, f2_file))):
                shutil.copytree(os.path.join(dir2, f2_file), os.path.join(dir1, f2_file))                

if __name__ == '__main__':

    if (len(sys.argv) == 3):
        dir1 = sys.argv[1]
        dir2 = sys.argv[2]
        if (not os.path.exists(dir1) and not os.path.exists(dir2)):
            print("Please make sure at least one directory exists")
        elif (not os.path.exists(dir1)):
            os.mkdir(dir1)
        elif (not os.path.exists(dir2)):
            os.mkdir(dir2)
        sync(dir1, dir2)
    else:
        print("Please provide a valid input")

    
            