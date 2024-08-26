import logging
from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from datetime import datetime
logging.basicConfig(level=logging.DEBUG)

client = MongoClient('localhost', 27017) #to interact with the database
db = client.jira_database
tasks_collection = db.tasks
users_collection = db.users
counters_collection = db.counters

def get_user_email(user_id):
    user = users_collection.find_one({"user_id": user_id}, {"user_email": 1})
    if user and 'user_email' in user:
        return user['user_email'].strip().lower()
    return None