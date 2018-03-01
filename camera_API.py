import db
import datetime
import bson
import bson.json_util
from bson.objectid import ObjectId
import json
import flask
import requests
import re
import threading

cam_status = {}
cam_status_lock = threading.Lock()

camera_api = flask.Blueprint('camera_api', __name__)
acceptable_time_diff = 60  # seconds
same_event_timespan = 5 * 60  # seconds


@camera_api.route('/camera_api/get_available_cam', methods=['GET'])
def cam_service_get_cam():
    def tend_cameras():
        cams = db.cam_collection.find()
        for cam in cams:
            id = str(cam['_id'])
            if cam['running']:
                reset = True
                if id in cam_status:
                    cam_run_data = cam_status[id]
                    how_long_ago = (datetime.datetime.utcnow() - cam_run_data['last_monitor_time'].
                                    replace(tzinfo=None)).total_seconds()
                    print ("{} {}".format(cam['camera_id'], how_long_ago))
                    if abs(how_long_ago) < acceptable_time_diff:
                        reset = False
                if reset:
                    cam['running'] = False
                    db.cam_collection.find_and_modify(query={'_id': cam['_id']}, update={'$set': {'running': False}})

    tend_cameras()
    cam_config = db.cam_collection.find_and_modify \
        (query={'running': False},
         update={'$set': {'running': True}})
    if cam_config:
        encoded = bson.json_util.dumps({'camera': cam_config})
    else:
        encoded = bson.json_util.dumps({'camera': None})
    return encoded


@camera_api.route('/camera_api/stop_cam', methods=['POST'])
def cam_service_stop_cam():
    data = json.loads(flask.request.data)
    cam_id = ObjectId(data['camera'])
    db.cam_collection.find_and_modify(query={'_id': cam_id},
                                      update={'$set': {'running': False}})
    return flask.jsonify({'ok': True})


@camera_api.route('/camera_api/heartbeat', methods=['POST'])
def cam_heartbeat():
    data = bson.json_util.loads(flask.request.data)
    with cam_status_lock:
        cam_status[str(data['_id'])] = data
    return flask.jsonify({'ok': True})


def move_queue_to_event(id=None):
    car_queue_data = [db.plate_read_queue.find_one({'_id': id})] if id is not None else db.plate_read_queue.find()
    for car in car_queue_data:
        db.plate_read_queue.delete_one(car)
        db.plate_read_queue_processed.save(car)
        if 'confidence' not in car:
            car['confidence'] = 70
        same_event = db.event_collection.find_one({'plate': car['plate'],
                                                'date_time': {
                                                    "$gte": car['date_time'] - datetime.timedelta(
                                                        seconds=same_event_timespan),
                                                    "$lte": car['date_time'] + datetime.timedelta(
                                                        seconds=same_event_timespan)
                                                }})
        if same_event is not None:
            if same_event['confidence'] < car['confidence']:
                same_event['image'] = car['image']
                same_event['confidence'] = car['confidence']
                db.event_collection.save(same_event)
        else:
            db.event_collection.insert_one(car)
            populate_car_list(car)


def populate_car_list(car):
    # car_view.remove({})
    seen_before = db.car_list_collection.find_one({'plate': car['plate']})
    if seen_before is None:
        new_car_view_entry = {}
        new_car_view_entry['plate'] = car['plate']
        new_car_view_entry['event_list'] = [car['_id']]
        new_car_view_entry['show'] = True
        new_car_view_entry['date_time'] = car['date_time']
        db.car_list_collection.save(new_car_view_entry)
    else:
        if car['_id'] not in seen_before['event_list']:
            seen_before['event_list'].append(car['_id'])
            seen_before['date_time'] = max(seen_before['date_time'], car['date_time'])
            seen_before['show'] = True
            db.car_list_collection.save(seen_before)
    process_alert(car['plate'])


def process_alert(plate):
    alerts = db.alerts_collection.find()
    outgoing = {}
    for alert in alerts:
        if re.match(alert['plate'], plate) is not None:
            if alert['email'] in outgoing:
                outgoing[alert['email']].append(alert['plate'])
            else:
                outgoing[alert['email']] = [alert['plate']]

    for email, alert_set in outgoing.items():
        requests.post(
            "https://api.mailgun.net/v3/sandbox67d23e2185634a7687582f219e2a6717.mailgun.org/messages",
            auth=("api", "key-847381bb57e3007caa20e8dd4be15aff"),
            data={"from": "Garage Alerts <postmaster@sandbox67d23e2185634a7687582f219e2a6717.mailgun.org>",
                  "to": email,
                  "subject": "Alert for Vehicle {}".format(plate),
                  "text": "Vehicle {} seen.  It was captured by the following alert(s): {}".format(plate,
                                                                                                   alert_set)})


@camera_api.route('/camera_api/event/save', methods=['POST'])
def cam_save_event():
    data = bson.json_util.loads(flask.request.data)
    id = db.plate_read_queue.insert_one({
        'plate': data['plate'],
        'image': db.fs.put(data['image']),
        'date_time': datetime.datetime.utcnow(),
        'confidence': data['confidence'],
        'raw_data': data['raw_data'],
        'camera_id': data['camera_id']}).inserted_id
    move_queue_to_event(id)
    return flask.jsonify({'ok': True})
