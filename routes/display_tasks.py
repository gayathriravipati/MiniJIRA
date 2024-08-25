import logging
from flask import Blueprint, request, jsonify
from pymongo import MongoClient
logging.basicConfig(level=logging.DEBUG)

client = MongoClient('localhost', 27017)
db = client.jira_database
tasks_collection = db.tasks
shared_tasks_collection = db.shared_tasks
display_tasks_bp = Blueprint('display_tasks', __name__)

@display_tasks_bp.route('/display_tasks/<int:user_id>', methods=['GET'])
def display_tasks(user_id):
    try:
        # Fetch tasks assigned to the user
        assigned_tasks = tasks_collection.find_one(
            {"user_id": user_id},
            {"tasks": 1}  
        )
        
        if not assigned_tasks:
            assigned_tasks = {"tasks": []}
        else:
            assigned_tasks = assigned_tasks.get('tasks', [])

        # Fetch shared tasks for the user
        shared_tasks_doc = shared_tasks_collection.find_one(
            {"shared_user_id": user_id}
        )
        
        if shared_tasks_doc:
            shared_tasks = shared_tasks_doc.get('shared_tasks', [])
            task_ids = [task['task_id'] for task in shared_tasks]

            # Fetch details of shared tasks
            shared_tasks_details = tasks_collection.find(
                {"tasks.task_id": {"$in": task_ids}},
                {"tasks.$": 1}  
            )
            
            shared_tasks_details = [task['tasks'][0] for task in shared_tasks_details]

        else:
            shared_tasks_details = []

        return jsonify({
            "assigned_tasks": assigned_tasks,
            "shared_tasks": shared_tasks_details
        }), 200

    except Exception as e:
        logging.error(f"Exception occurred while fetching tasks: {str(e)}")
        return jsonify({"error": str(e)}), 500