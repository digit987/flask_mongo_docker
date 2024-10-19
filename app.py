import os
from bson import ObjectId
from cerberus import Validator
from dotenv import load_dotenv
from flask import Flask, g, jsonify, request
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

load_dotenv()

app = Flask(__name__)

DATABASE_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = 'userDb'

def get_db():
    if 'db' not in g:
        client = MongoClient(DATABASE_URI)
        g.db = client[DATABASE_NAME]
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.client.close()

user_schema = {
    'name': {'type': 'string', 'maxlength': 100, 'required': True},
    'email': {'type': 'string', 'regex': r'[^@]+@[^@]+\.[^@]+', 'required': True},
    'age': {'type': 'integer', 'min': 0, 'max': 120, 'required': False},
    'password': {'type': 'string', 'minlength': 8, 'maxlength': 64, 'required': True}
}

validator = Validator(user_schema)

@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.json
    if validator.validate(data):
        data['password'] = generate_password_hash(data['password'])
        db = get_db()
        result = db.users.insert_one(data)
        return jsonify({'message': 'User successfully added', 'user_id': str(result.inserted_id)}), 201
    else:
        return jsonify({'error': validator.errors}), 400

@app.route('/get_user/<user_id>', methods=['GET'])
def get_user(user_id):
    db = get_db()
    user = db.users.find_one({'_id': ObjectId(user_id)})
    if user:
        user['_id'] = str(user['_id'])
        return jsonify({'message': user}), 200
    return jsonify({'error': 'User not found'}), 404

@app.route('/get_users', methods=['GET'])
def get_users():
    db = get_db()
    users = list(db.users.find())
    if users:
        for user in users:
            user['_id'] = str(user['_id'])
        return jsonify({'message': users}), 200
    return jsonify({'error': 'Users not found'}), 404

@app.route('/update_user/<user_id>', methods=['PUT'])
def update_user(user_id):
    db = get_db()
    data = request.json

    result = db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': data}
    )

    if result.matched_count > 0:
        return jsonify({"message": "User updated successfully"}), 200
    else:
        return jsonify({"error": "User not found"}), 404

@app.route('/delete_user/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    db = get_db()
    result = db.users.delete_one({'_id': ObjectId(user_id)})

    if result.deleted_count > 0:
        return jsonify({"message": "User deleted successfully"}), 200
    else:
        return jsonify({"error": "User not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)