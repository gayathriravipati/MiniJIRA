from flask import Blueprint, render_template
from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client.jira_database
users_collection = db.users

index_bp = Blueprint('index', __name__)

@index_bp.route('/')
def index():
    users = users_collection.find()
    return render_template('index.html', users=users)