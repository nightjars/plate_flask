import flask_plate
import datetime
from bson.objectid import ObjectId
import json
import flask
import re
import flask_jwt
import dateutil.parser
import pymongo
import camera_API

vehicle_api = flask.Blueprint('vehicle_api', __name__)


def mangle_id(input):
    input['id'] = str(input['_id'])
    del input['_id']
    if 'image' in input:
        input['image'] = str(input['image'])


@vehicle_api.route('/api/vehicle/recent')
@flask_jwt.jwt_required()
def get_garages():
    now = datetime.datetime.now()
    all_cars = flask_plate.db.car_list_collection.find({"show": True}).sort("date_time", pymongo.DESCENDING)
    vehicles = []
    for car in all_cars:
        vehicle_data = flask_plate.db.car_list_collection.find_one({"_id": ObjectId(car['_id'])})
        newest_event = flask_plate.db.event_collection.find_one({"_id": ObjectId(vehicle_data['event_list'][-1])})
        alerts_present = False if flask_plate.db.alerts_collection.find_one({"plate": car['plate']}) is None else True
        vehicles.append({'plate': car['plate'],
                         'date_time': car['date_time'],
                         'newest_image': str(newest_event['image']),
                         'id': str(car['_id']),
                         'note': car['note'] if 'note' in car else '',
                         'alerts': alerts_present})
    counts = {
        '24h': flask_plate.db.event_collection.find({'date_time': {"$gt": datetime.datetime.utcnow() -
                                                           datetime.timedelta(days=1)}}).count(),
        '1w': flask_plate.db.event_collection.find({'date_time': {"$gt": datetime.datetime.utcnow() -
                                                           datetime.timedelta(days=7)}}).count(),
        '1mo': flask_plate.db.event_collection.find({'date_time': {"$gt": datetime.datetime.utcnow() -
                                                             datetime.timedelta(days=30)}}).count(),
    }
    response = flask.jsonify({'vehicles': vehicles,
                              'counts': counts})
    # response.headers.add('Access-Control-Allow-Origin', '*')
    print ("time fetching garage data: {} seconds".format((datetime.datetime.now()-now).total_seconds()))
    return response


@vehicle_api.route('/api/vehicle/search', methods=['GET'])
@flask_jwt.jwt_required()
def search_vehicle():
    start_date = flask.request.args.get('start_date', default='', type=str)
    end_date = flask.request.args.get('end_date', default='', type=str)
    plate_substring = flask.request.args.get('plate_substring', default='', type=str)
    note = flask.request.args.get('note', default='', type=str)
    include_thumbnails = flask.request.args.get('include_thumbnails', default=False, type=bool)
    if not len(start_date.strip()):
        start_date = '1/1/1700'
    if not len(end_date.strip()):
        end_date = '1/1/2100'

    plate_regex = '.*{}.*'.format(plate_substring) if len(plate_substring) else '.*'
    note_regex = '.*{}.*'.format(note) if len(note) else '.*'

    time_from_utc = datetime.datetime.now() - datetime.datetime.utcnow()

    all_events = flask_plate.db.event_collection.find({'$and': [{'date_time': {'$gte': dateutil.parser.parse(start_date)
                                                                        - time_from_utc}},
                                                 {'date_time': {'$lte': dateutil.parser.parse(end_date)
                                                                        - time_from_utc + datetime.timedelta(days=1)}},
                                                 {'plate': {'$regex': plate_regex, '$options': 'i'}}]}).\
                                                  sort("date_time", pymongo.DESCENDING)

    event_list = []
    for event in all_events:
        vehicle_data = flask_plate.db.car_list_collection.find_one({"plate": event['plate']})
        if len(note) and 'note' in vehicle_data and re.search(note_regex, vehicle_data['note'],
                                                              flags=re.IGNORECASE) is None:
            pass
        elif len(note) and 'note' not in vehicle_data:
            pass
        else:
            alerts_present = False if flask_plate.db.alerts_collection.find_one({"plate": event['plate']}) is None else True
            event_list.append({'plate': event['plate'],
                               'date_time': event['date_time'],
                               'id': str(event['_id']),
                               'image': str(event['image']) if include_thumbnails else None,
                               'note': vehicle_data['note'] if 'note' in vehicle_data else '',
                               'alerts': alerts_present})
    return flask.jsonify({'results': list(event_list)})


@vehicle_api.route('/api/vehicle/delete', methods=['POST'])
@flask_jwt.jwt_required()
def delete_vehicle():
    user = flask_jwt.current_identity
    if user.writeAccess:
        data = json.loads(flask.request.data)
        vehicle = flask_plate.db.car_list_collection.find_one({"_id": ObjectId(data['id'])})
        if vehicle is not None:
            vehicle["show"] = False
            flask_plate.db.car_list_collection.save(vehicle)
        response = flask.Response()
        return response
    else:
        return flask.Response('User does not have write access.', 401)


@vehicle_api.route('/api/vehicle/set_note', methods=['POST'])
@flask_jwt.jwt_required()
def set_note():
    user = flask_jwt.current_identity
    if user.writeAccess:
        data = json.loads(flask.request.data)
        vehicle = flask_plate.db.car_list_collection.find_one({"_id": ObjectId(data['id'])})
        if vehicle is not None and 'note' in data:
            vehicle['note'] = data['note']
            flask_plate.db.car_list_collection.save(vehicle)
        response = flask.Response()
        return response
    else:
        return flask.Response('User does not have write access.', 401)


@vehicle_api.route('/api/vehicle/details/<vehicle_id>', methods=['GET'])
@flask_jwt.jwt_required()
def details_vehicle(vehicle_id):
    vehicle = flask_plate.db.car_list_collection.find_one({"_id": ObjectId(vehicle_id)})
    if vehicle is None:
        event_vehicle = flask_plate.db.event_collection.find_one({"_id": ObjectId(vehicle_id)})
        if event_vehicle is not None:
            vehicle = flask_plate.db.car_list_collection.find_one({"plate": event_vehicle['plate']})
    if vehicle is not None:
        if 'note' not in vehicle:
            vehicle['note'] = ''

        events = []
        mangle_id(vehicle)
        for event in reversed(vehicle['event_list']):
            events.append(flask_plate.db.event_collection.find_one({"_id": ObjectId(event)}))
            mangle_id(events[-1])
            if 'camera_id' in events[-1]:
                del events[-1]['camera_id']
        alerts_present = False if flask_plate.db.alerts_collection.find_one({"plate": vehicle['plate']}) is None else True
        vehicle['event_list'] = events
        vehicle['alerts'] = alerts_present
        return flask.jsonify(vehicle)
    else:
        return None


@vehicle_api.route('/api/vehicle/alert/create', methods=['POST'])
@flask_jwt.jwt_required()
def create_alert():
    user = flask_jwt.current_identity
    if user.writeAccess:
        data = json.loads(flask.request.data)
        alert = {'plate': data['plate'],
                 'email': data['email']}
        flask_plate.db.alerts_collection.save(alert)
        return flask.jsonify({'ok': True})
    else:
        return flask.jsonify({'ok': False})


@vehicle_api.route('/api/vehicle/alert/delete', methods=['POST'])
@flask_jwt.jwt_required()
def delete_alert():
    user = flask_jwt.current_identity
    if user.writeAccess:
        data = json.loads(flask.request.data)
        flask_plate.db.alerts_collection.delete_one({'_id': ObjectId(data['id'])})
        return flask.jsonify({'ok': True})
    else:
        return flask.jsonify({'ok': False})


@vehicle_api.route('/api/vehicle/alert/get', methods=['GET'], defaults={'plate': None})
@vehicle_api.route('/api/vehicle/alert/get/<plate>', methods=['GET'])
@flask_jwt.jwt_required()
def get_alerts(plate):
    if plate is None:
        result = flask_plate.db.alerts_collection.find()
    else:
        result = flask_plate.db.alerts_collection.find({'plate': plate})
    response = []
    for entry in result:
        response.append({'plate': entry['plate'], 'id': str(entry['_id']), 'email': entry['email']})
    return flask.jsonify(response)


@vehicle_api.route('/api/vehicle/get_event/<event_id>', methods=['GET'])
@flask_jwt.jwt_required()
def get_event(event_id):
    event = flask_plate.db.event_collection.find_one({'_id': ObjectId(event_id)})
    if event:
        event['id'] = str(event['_id'])
        del event['_id']
        event['camera_id'] = str(event['camera_id']) if 'camera_id' in event else "db needs refactoring"
        event['image'] = str(event['image'])
        return flask.jsonify(event)
    else:
        flask.abort(404)


@vehicle_api.route('/api/vehicle/correct_plate', methods=['POST'])
@flask_jwt.jwt_required()
def correct_plate():
    user = flask_jwt.current_identity
    if user.writeAccess:
        data = json.loads(flask.request.data)
        event = flask_plate.db.event_collection.find_one({'_id': ObjectId(data['id'])})
        vehicle_entry = flask_plate.db.car_list_collection.find_one({'plate': event['plate']})
        vehicle_entry['event_list'].remove(ObjectId(data['id']))
        if len(vehicle_entry['event_list']):
            flask_plate.db.car_list_collection.save(vehicle_entry)
        else:
            flask_plate.db.car_list_collection.delete_one({'_id': vehicle_entry['_id']})
        event['plate'] = data['plate']
        flask_plate.db.plate_read_queue.save(event)
        flask_plate.db.event_collection.delete_one({'_id': event['_id']})
        flask_plate.db.plate_read_queue_processed.delete_one({'_id': event['_id']})
        camera_API.move_queue_to_event(id=event['_id'])
        return flask.jsonify({'ok': True})
    else:
        return flask.jsonify({'ok': False})