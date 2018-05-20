import werkzeug.security
from bson.objectid import ObjectId
import flask
import flask_jwt
import json
import db


user_api = flask.Blueprint('user_api', __name__)


def authenticate(username, password):
    user = db.db.users_collection.find_one({'username': username})
    if user and werkzeug.security.check_password_hash(user['password'], password):
        return User(**user)


def identity(payload):
    user_id = payload['identity']
    return User(**db.db.users_collection.find_one({'_id': ObjectId(user_id)}))

import flask_plate

class User(object):
    def __init__(self, username="", password="", _id=None, writeAccess=False, adminAccess=False):
        self.id = str(_id)
        self.username = username.strip()
        self.password = password.strip()
        self.writeAccess = writeAccess
        self.adminAccess = adminAccess

    def clear_password(self):
        self.password = ''


@user_api.route('/api/user/change_password', methods=['POST'])
@flask_jwt.jwt_required()
def change_password():
    data = json.loads(flask.request.data)
    user = flask_jwt.current_identity
    fail_reason = ""
    if user.authenticate(user.username, data['currentPassword']):
        user = flask_plate.db.users_collection.find_one({'username': user.username})
        if 'newPassword' in data and len(data['newPassword']) > 4:
            user['password'] = werkzeug.security.generate_password_hash(data['newPassword'])
            flask_plate.db.users_collection.save(user)
            return flask.jsonify({'ok': True})
        else:
            fail_reason = "New password too short."
    else:
        fail_reason = "Current password incorrect."
    return flask.jsonify({'ok': False, 'error': fail_reason})


@user_api.route('/api/user/user_permissions', methods=['GET'])
@flask_jwt.jwt_required()
def get_permissions():
    user = flask_jwt.current_identity
    user = User(**flask_plate.db.users_collection.find_one({'username': user.username}))
    return flask.jsonify({'writeAccess': user.writeAccess, 'adminAccess': user.adminAccess})


@user_api.route('/api/user/create_user', methods=['POST'])
@flask_jwt.jwt_required()
def create_user():
    user = flask_jwt.current_identity
    if user.adminAccess:
        fail = False
        fail_reason = ""
        data = json.loads(flask.request.data)
        user = vars(User(**data))
        del(user['id'])
        if len(user['password']) < 5:
            fail = True
            fail_reason = "Password too short."
        if len(user['username']) < 5:
            fail_reason = "Username too short."
        if not fail:
            if flask_plate.db.users_collection.find({'username': user['username']}).count() == 0:
                user['password'] = werkzeug.security.generate_password_hash(user['password'])
                flask_plate.db.users_collection.save(user)
                return flask.jsonify({'ok': True})
            else:
                fail = True
                fail_reason = "Username already in use.  Please try again."
        return flask.jsonify({'ok': False, 'error': fail_reason})


@user_api.route('/api/user/users', methods=['GET'])
@flask_jwt.jwt_required()
def get_users():
    user = flask_jwt.current_identity
    if user.adminAccess:
        users = flask_plate.db.users_collection.find()
        user_list = []
        for user in users:
            userObj = User(**user)
            userObj.clear_password()
            user_list.append(vars(userObj))
        return flask.jsonify(user_list)


@user_api.route('/api/user/modify_user', methods=['POST'])
@flask_jwt.jwt_required()
def modify_user():
    user = flask_jwt.current_identity
    if user.adminAccess:
        data = json.loads(flask.request.data)
        db_user = flask_plate.db.users_collection.find_one({'username': data['username']})
        if len(db_user):
            for key, value in data.items():
                if key == 'password' and value is not None and len(value):
                    db_user['password'] = werkzeug.security.generate_password_hash(value)
                if key == 'writeAccess' or key == 'adminAccess':
                    db_user[key] = value
            flask_plate.db.users_collection.save(db_user)
            return flask.jsonify({'ok': True})
        else:
            return flask.jsonify({'ok': False})


@user_api.route('/api/user/delete_user', methods=['POST'])
@flask_jwt.jwt_required()
def delete_user():
    user = flask_jwt.current_identity
    if user.adminAccess:
        data = json.loads(flask.request.data)
        if flask_plate.db.users_collection.find({'username': data['username']}).count() == 1:
            flask_plate.db.users_collection.delete_one({'username': data['username']})
            return flask.jsonify({'ok': True})
        return flask.jsonify({'ok': False})


#user = users_collection.find_one({'username': 'dave'})
#user['password'] = werkzeug.security.generate_password_hash('goat')
#del user['id']
#users_collection.save(user)
