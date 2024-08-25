import logging
from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from routes.utils.utils import get_user_email

# Configure logging
logging.basicConfig(level=logging.DEBUG)

client = MongoClient('localhost', 27017)
db = client.jira_database
tasks_collection = db.tasks

close_tasks_bp = Blueprint('close_tasks', __name__)

@close_tasks_bp.route('/close_task/<int:user_id>/<int:task_id>', methods=['POST'])
def close_task(user_id, task_id):
    try:
        # Fetch the task with the given user_id and task_id
        user_document = tasks_collection.find_one(
            {"user_id": user_id, "tasks.task_id": task_id},
            {"tasks.$": 1}  
        )

        if not user_document or not user_document.get('tasks'):
            return jsonify({"error": "Task not found or you do not have permission to close this task"}), 403
        
        task_to_close = user_document['tasks'][0]
        created_by_email = task_to_close.get('created_by')
        request_user_email = get_user_email(user_id)

        if not request_user_email:
            return jsonify({"error": "User not found or missing email"}), 400

        # Check if the user is the creator of the task
        if created_by_email != request_user_email:
            return jsonify({"error": "You do not have permission to close this task"}), 403

        # Update the task status to CLOSED
        result = tasks_collection.update_one(
            {"user_id": user_id, "tasks.task_id": task_id},
            {"$set": {"tasks.$.status": "CLOSED"}}
        )

        if result.modified_count == 0:
            return jsonify({"error": "Failed to close the task"}), 500

        return jsonify({"message": "Task closed successfully"}), 200

    except Exception as e:
        logging.error(f"Exception occurred while closing task: {str(e)}")
        return jsonify({"error": str(e)}), 500