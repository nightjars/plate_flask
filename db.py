import bson
import bson.json_util
import gridfs
import pymongo

client = pymongo.MongoClient('192.168.1.99')
db = client['plate-db']
event_collection = db['events']
car_list_collection = db['car-view']
users_collection = db['users']
alerts_collection = db['alerts']
cam_collection = db['camera-config']
plate_read_queue = db['plate-read-queue']
plate_read_queue_processed = db['plate-read-queue-processed']
fs = gridfs.GridFS(db)
