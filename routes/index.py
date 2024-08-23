from flask import Blueprint, jsonify
from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client.jira_database
users_collection = db.users

index_bp = Blueprint('index', __name__)

@index_bp.route('/')
def index():
    try:
        users_cursor = users_collection.find()
        users = list(users_cursor)
        
        # Convert MongoDB ObjectId to string for JSON serialization
        for user in users:
            user['_id'] = str(user['_id'])
        
        return jsonify(users), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
