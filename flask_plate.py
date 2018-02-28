from flask import Flask
from flask_cors import CORS
import datetime
import flask_jwt
import user_API
import camera_API
import camera_user_API
import vehicle_API
import image_API


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


if __name__ == '__main__':
    app.run(host='192.168.1.99', threaded=True)
