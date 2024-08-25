import logging
from flask import Blueprint, request, jsonify
from pymongo import MongoClient

# Configure logging
logging.basicConfig(level=logging.DEBUG)

client = MongoClient('localhost', 27017)
db = client.jira_database
tasks_collection = db.tasks
shared_tasks_collection = db.shared_tasks

filter_tasks_bp = Blueprint('filter_tasks', __name__)

@filter_tasks_bp.route('/filter_tasks/<int:user_id>', methods=['GET'])
def filter_tasks(user_id):
    try:
        status = request.args.get('status')
        logging.debug(f"Received filter request for user {user_id} with status {status}")

        if not status:
            return jsonify({"error": "Query parameter 'status' is required"}), 400

        status = status.upper()
        if status not in ["CLOSED", "DELAYED"]:
            return jsonify({"error": "Invalid status value. Must be 'closed' or 'delayed'"}), 400

        # Fetch tasks assigned to the user with the given status
        assigned_tasks = tasks_collection.find_one(
            {"user_id": user_id, "tasks.status": status},
            {"tasks": {"$elemMatch": {"status": status}}}
        )

        assigned_tasks_list = assigned_tasks['tasks'] if assigned_tasks and 'tasks' in assigned_tasks else []

        # Fetch tasks shared with the user that have the given status
        shared_task_entries = shared_tasks_collection.find({"shared_user_id": user_id})
        shared_tasks_list = []

        for entry in shared_task_entries:
            task_owner_id = entry['task_owner_id']
            task_id = entry['task_id']

            # Fetch the actual task from the task owner's document
            task_owner_document = tasks_collection.find_one(
                {"user_id": task_owner_id, "tasks.task_id": task_id, "tasks.status": status},
                {"tasks.$": 1}
            )
            if task_owner_document and 'tasks' in task_owner_document:
                shared_tasks_list.append(task_owner_document['tasks'][0])

        # Combine both lists
        all_tasks = assigned_tasks_list + shared_tasks_list

        return jsonify({"tasks": all_tasks}), 200

    except Exception as e:
        logging.error(f"Exception occurred while filtering tasks: {str(e)}")
        return jsonify({"error": str(e)}), 500
