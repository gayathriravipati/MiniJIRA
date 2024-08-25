import logging
from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from datetime import datetime
from routes.utils.utils import get_user_email

# Configure logging
logging.basicConfig(level=logging.DEBUG)

client = MongoClient('localhost', 27017)
db = client.jira_database
tasks_collection = db.tasks
users_collection = db.users
counters_collection = db.counters
edit_tasks_bp = Blueprint('edit_tasks', __name__)

@edit_tasks_bp.route('/edit_tasks/<int:task_id>/<int:user_id>', methods=['POST'])
def edit_task(task_id, user_id):
    try:
        data = request.json
        logging.debug(f"Received data for editing task {task_id} by user {user_id}: {data}")

        if not data:
            return jsonify({"error": "Request body is missing or invalid"}), 400

        # Check if the task_id exists in the tasks array for the given user_id
        user_document = tasks_collection.find_one({
            "user_id": user_id,
            "tasks.task_id": task_id
        }, {
            "tasks.$": 1  # Projection to only return the matching task
        })

        if not user_document or not user_document.get('tasks'):
            return jsonify({"error": "Task not found or you do not have permission to edit this task"}), 403
        
        task_to_edit = user_document['tasks'][0]
        created_by_email = task_to_edit.get('created_by')
        request_user_email = get_user_email(user_id)
        if not request_user_email:
            return jsonify({"error": "User not found or missing email"}), 400

        # Check if the user is the creator of the task
        if created_by_email != request_user_email:
            return jsonify({"error": "You do not have permission to edit this task"}), 403

        update_fields = {}

        # Validate and update the timeline if provided
        if 'timeline' in data:
            timeline_str = data['timeline']
        try:
            timeline = datetime.strptime(timeline_str, '%m-%d-%Y')
        except ValueError:
            return jsonify({"error": "Invalid date format for timeline, should be MM-DD-YYYY"}), 400
        
        # Timeline must be in the future
        if timeline <= datetime.now():
            return jsonify({"error": "Timeline must be a future date"}), 400
        
        update_fields["tasks.$.timeline"] = timeline

        # Validate and update the title if provided
        if 'title' in data:
            update_fields["tasks.$.title"] = data['title']

        # Validate and update the description if provided
        if 'description' in data:
            update_fields["tasks.$.description"] = data['description']

        # Validate and update the URL list if provided
        if 'URL' in data:
            if not isinstance(data['URL'], list):
                return jsonify({"error": "URL must be a list"}), 400
            update_fields["tasks.$.URL"] = data['URL']

        # Validate and update the share_to list if provided
        if 'share_to' in data:
            if not isinstance(data['share_to'], list):
                return jsonify({"error": "share_to must be a list"}), 400

            valid_emails = set()
            try:
                user_emails = users_collection.find({}, {"user_email": 1})
                for user in user_emails:
                    if 'user_email' in user:
                        email = user['user_email'].strip().lower()
                        valid_emails.add(email)
                    else:
                        logging.warning("User document missing 'user_email' field: %s", user)
            except Exception as e:
                logging.error("Failed to fetch users: %s", str(e))
                return jsonify({"error": "Failed to validate email addresses"}), 500

            share_to_normalized = [email.strip().lower() for email in data['share_to']]
            invalid_emails = [email for email in share_to_normalized if email not in valid_emails]

            if invalid_emails:
                logging.debug(f"Invalid emails: {invalid_emails}")
                return jsonify({
                    "error": "Invalid email addresses in share_to",
                    "invalid_emails": invalid_emails
                }), 400

            update_fields["tasks.$.share_to"] = share_to_normalized

        # Proceed with the update if there are valid fields to update
        if update_fields:
            result = tasks_collection.update_one(
                {"user_id": user_id, "tasks.task_id": task_id},
                {"$set": update_fields}
            )
            if result.modified_count == 0:
                return jsonify({"error": "No changes were made"}), 500

        return jsonify({"message": "Task updated successfully"}), 200

    except Exception as e:
        logging.error(f"Exception occurred while editing task: {str(e)}")
        return jsonify({"error": str(e)}), 500
