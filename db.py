import bson
import bson.json_util
import gridfs
import pymongo


class db(object):
    def __init__(self, host):
        self.client = pymongo.MongoClient(host)
        self.db = self.client['plate-db']
        self.event_collection = self.db['events']
        self.car_list_collection = self.db['car-view']
        self.users_collection = self.db['users']
        self.alerts_collection = self.db['alerts']
        self.cam_collection = self.db['camera-config']
        self.plate_read_queue = self.db['plate-read-queue']
        self.plate_read_queue_processed = self.db['plate-read-queue-processed']
        self.fs = gridfs.GridFS(self.db)
