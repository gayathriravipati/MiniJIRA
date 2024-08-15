from flask import Blueprint, request, jsonify, redirect, url_for
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

client = MongoClient('localhost', 27017)
db = client.jira_database
users_collection = db.users
counters_collection = db.counters

add_user_bp = Blueprint('add_user', __name__)

# Counter to keep track of the number of users
def get_next_user_id():
    counter = counters_collection.find_one_and_update(
        {"_id": "user_id"},
        {"$inc": {"seq": 1}},
        return_document=True
    )
    return counter['seq']

def insert_user(user_email):
    user_id = get_next_user_id()
    user_document = {
        'user_id': user_id,
        'user_email': user_email
    }
    users_collection.insert_one(user_document)

@add_user_bp.route('/add_user', methods=['POST'])
def add_user():
    user_email = request.form.get('user_email')

    if not user_email:
        return jsonify({'error': 'Email is required'}), 400

    if users_collection.find_one({'user_email': user_email}):
        return jsonify({'error': 'Email already exists'}), 409

    try:
        insert_user(user_email)
        return jsonify({'message': 'User added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return redirect(url_for('index'))