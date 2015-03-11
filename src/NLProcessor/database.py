__author__="Karan S. Sisodia"
__email__="karansinghsisodia@gmail.com"
__date__ ="$Jun 6, 2014 9:01:10 AM$"

import peewee
import datetime
from peewee import *
from app import *

from pymongo import MongoClient

# Configuration File
Config = Config()

class Database():
    
    def connect(self):
        client = MongoClient(str(Config.get('MongoDB')['host']), int(Config.get('MongoDB')['port']))
        db = client['NER']
        return db
