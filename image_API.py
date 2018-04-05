import flask
import io
from bson.objectid import ObjectId
import flask_plate

image_api = flask.Blueprint('image_api', __name__)


@image_api.route('/image/<image_id>')
def get_image(image_id):
    return flask.send_file(io.BytesIO(flask_plate.db.fs.get(ObjectId(image_id)).read()),
                           mimetype='image/jpg')
