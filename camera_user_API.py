import flask
import flask_jwt
import copy
import camera_API
import bson
import bson.json_util
import image_processing
from bson.objectid import ObjectId
import PIL
import io
import json
import db


camera_user_api = flask.Blueprint('camera_user_api', __name__)


@camera_user_api.route('/api/camera/get', methods=['GET'])
@flask_jwt.jwt_required()
def get_cameras():
    cameras = []
    cam_db = db.cam_collection.find()
    for cam in cam_db:
        cam['id'] = str(cam['_id'])
        if cam['id'] in camera_API.cam_status:
            with camera_API.cam_status_lock:
                cam['run_status'] = copy.deepcopy(camera_API.cam_status[cam['id']])
        del cam['_id']
        del cam['run_status']['_id']
        if 'mask_image' in cam:
            del cam['mask_image']
        if 'run_status' in cam and cam['run_status'] is not None and 'latest_image' in cam['run_status']:
            del cam['run_status']['latest_image']
        cameras.append(cam)
    return flask.jsonify(cameras)


@camera_user_api.route('/api/camera/get/image/<camera_id>')
def get_cam_image(camera_id):
    if camera_id in camera_API.cam_status:
        cam = camera_API.cam_status[camera_id]
        return flask.Response(cam['latest_image'], mimetype='image/jpg')
    return flask.Response(None)


@camera_user_api.route('/api/camera/get/image_json/<camera_id>')
def get_cam_image_json(camera_id):
    if camera_id in camera_API.cam_status:
        cam = camera_API.cam_status[camera_id]
        return bson.json_util.dumps({'image': cam['latest_image']})
    return bson.json_util.dumps({'image': None})


@camera_user_api.route('/api/camera/get/motion_image/<camera_id>')
def get_cam_motion_image(camera_id):
    cam = db.cam_collection.find_one({'_id': ObjectId(camera_id)})
    if cam is not None:
        if camera_id in camera_API.cam_status:
            cam_img_bytes = camera_API.cam_status[camera_id]['latest_image']
            if 'mask_image' in cam:
                mask_img_bytes = cam['mask_image']
                cam_img = PIL.Image.open(io.BytesIO(cam_img_bytes))
                mask_img = PIL.Image.open(io.BytesIO(mask_img_bytes))
                image_processing.mask_image(cam_img, mask_img)
                return flask.Response(image_processing.mask_image(cam_img, mask_img), mimetype='image/jpg')
    return flask.Response(None)


@camera_user_api.route('/api/camera/get/sample_motion_image')
def sample_motion_image():
    x1 = flask.request.args.get('x1', default=None, type=int)
    x2 = flask.request.args.get('x2', default=None, type=int)
    y1 = flask.request.args.get('y1', default=None, type=int)
    y2 = flask.request.args.get('y2', default=None, type=int)
    id = flask.request.args.get('id', default=None, type=str)
    if x1 is not None or x2 is not None or y1 is not None or y2 is not None or id is not None:
        cam = db.cam_collection.find_one({'_id': ObjectId(id)})
        if cam is not None:
            if cam['running']:
                if id in camera_API.cam_status:
                    cam_img_bytes = camera_API.cam_status[id]['latest_image']
                    cam_img = PIL.Image.open(io.BytesIO(cam_img_bytes))
                    mask_img = PIL.Image.open(io.BytesIO(image_processing.create_mask_image(x1, y1, x2, y2)))
                    return flask.Response(image_processing.mask_image(cam_img, mask_img), mimetype='image/jpg')
    return flask.Response(None)


@camera_user_api.route('/api/camera/save', methods=['POST'])
@flask_jwt.jwt_required()
def save_cameras():
    data = json.loads(flask.request.data)
    user = flask_jwt.current_identity
    if user.adminAccess:
        print (data)
        id = ObjectId(data['id'])
        print (id)
        return flask.jsonify({'ok': True})
    return flask.jsonify({'ok': False, 'error': "Requires admin access."})


@camera_user_api.route('/api/camera/set_detection_area', methods=['POST'])
@flask_jwt.jwt_required()
def set_camera_detection_area():
    data = json.loads(flask.request.data)
    user = flask_jwt.current_identity
    if user.adminAccess:
        cam = db.cam_collection.find_one({'_id': ObjectId(data['camera_id'])})
        if cam:
            cam['mask_image'] = image_processing.create_mask_image(data['x1'], data['y1'], data['x2'], data['y2'])
            db.cam_collection.save(cam)
            return flask.jsonify({'ok': True})
        return flask.jsonify({'ok': False, 'error': "Error loading camera."})
    return flask.jsonify({'ok': False, 'error': "Requires admin access."})
