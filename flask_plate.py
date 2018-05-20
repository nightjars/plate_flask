from flask import Flask
from flask_cors import CORS
import datetime
import flask_jwt
import user_API
import camera_API
import camera_user_API
import vehicle_API
import image_API
import argparse
import db
import reports_API

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'my_goat_has_thumbs'
app.config['JWT_EXPIRATION_DELTA'] = datetime.timedelta(minutes=120)
app.register_blueprint(camera_API.camera_api)
app.register_blueprint(camera_user_API.camera_user_api)
app.register_blueprint(user_API.user_api)
app.register_blueprint(vehicle_API.vehicle_api)
app.register_blueprint(image_API.image_api)
jwt = flask_jwt.JWT(app, user_API.authenticate, user_API.identity)

parser = argparse.ArgumentParser()
parser.add_argument('--db', help='IP address of MongoDB server')
parser.add_argument('--host', help='IP address to bind API server to')
db = db.db(parser.parse_args().db)

if __name__ == '__main__':
    app.run(host=parser.parse_args().host, threaded=True)
