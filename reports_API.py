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

reports_api = flask.Blueprint('reports_api', __name__)


@reports_api.route('/api/vehicle/report_by_freq')
@flask_jwt.jwt_required()
def get_report_by_freq():
    report = []
    for plate in flask_plate.db.event_collection.find().distinct('plate'):
        report.append((plate, flask_plate.db.event_collection.find({'plate': plate}).count()))
    response = flask.jsonify({'results': report})
    return response