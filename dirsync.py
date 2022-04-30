from genericpath import getmtime
import hashlib
import os
import datetime
from time import gmtime, strftime

def gen_hash(filename):
    sha256_hash = hashlib.sha256()
    with open (filename, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b''):
            sha256_hash.update(byte_block)
        print(sha256_hash.hexdigest())

def modified_time(filename):
    time = os.path.getmtime(filename)
    date = datetime.datetime.fromtimestamp(int(time)).strftime('%Y-%m-%d %H:%M:%S')
    timezone = strftime('%z', gmtime())
    return str(date) + str(timezone)

if __name__ == '__main__':
    print(modified_time('test.txt'))
    gen_hash('test.txt')