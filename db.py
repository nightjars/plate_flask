import bson
import bson.json_util
import gridfs
import pymongo

class db(object):
    def __init__(self, host):
        client = pymongo.MongoClient(host)
        db.db = client['plate-db']
        db.event_collection = db.db['events']
        db.car_list_collection = db.db['car-view']
        db.users_collection = db.db['users']
        db.alerts_collection = db.db['alerts']
        db.cam_collection = db.db['camera-config']
        db.plate_read_queue = db.db['plate-read-queue']
        db.plate_read_queue_processed = db.db['plate-read-queue-processed']
        db.fs = gridfs.GridFS(db.db)
