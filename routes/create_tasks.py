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
shared_tasks_collection = db.shared_tasks

create_tasks_bp = Blueprint('create_tasks', __name__)

def get_next_task_id():
    counter = counters_collection.find_one_and_update(
        {"_id": "task_id"},
        {"$inc": {"sequence_value": 1}},
        return_document=True,
        upsert=True
    )
    return counter['sequence_value']

@create_tasks_bp.route('/create_tasks', methods=['POST'])
def create_tasks():
    try:
        data = request.json
        logging.debug(f"Received data: {data}")

        if not data:
            return jsonify({"error": "Request body is missing or invalid"}), 400

        if 'user_id' not in data or not data['user_id']:
            return jsonify({"error": "user_id is required"}), 400
        if 'timeline' not in data or not data['timeline']:
            return jsonify({"error": "timeline is required"}), 400
        if 'title' not in data or not data['title']:
            return jsonify({"error": "title is required"}), 400

        user_id = data['user_id']
        timeline_str = data['timeline']
        title = data['title']
        #optional - fields
        description = data.get('description', '')
        url = data.get('URL', [])
        share_to = data.get('share_to', [])

        #time-line should follow format - MM-DD-YYYY and should be in the future
        try:
            timeline = datetime.strptime(timeline_str, '%m-%d-%Y')
        except ValueError:
            return jsonify({"error": "Invalid date format for timeline, should be MM-DD-YYYY"}), 400
        
        if timeline <= datetime.now():
            return jsonify({"error": "Timeline must be a future date"}), 400

        if not isinstance(url, list):
            return jsonify({"error": "URL must be a list"}), 400
        if not isinstance(share_to, list):
            return jsonify({"error": "share_to must be a list"}), 400

        if share_to:
            valid_emails = set()
            email_to_user_id = {}
            try:
                user_emails = users_collection.find({}, {"user_email": 1, "user_id": 1})
                for user in user_emails:
                    if 'user_email' in user and 'user_id' in user:
                        email = user['user_email'].strip().lower()
                        valid_emails.add(email)
                        email_to_user_id[email] = user['user_id']
                    else:
                        logging.warning("User document missing 'user_email' or 'user_id' field: %s", user)
            except Exception as e:
                logging.error("Failed to fetch users: %s", str(e))
                return jsonify({"error": "Failed to validate email addresses"}), 500

            share_to_normalized = [email.strip().lower() for email in share_to]
            invalid_emails = [email for email in share_to_normalized if email not in valid_emails]

            if invalid_emails:
                logging.debug(f"Invalid emails: {invalid_emails}")
                return jsonify({
                    "error": "Invalid email addresses in share_to",
                    "invalid_emails": invalid_emails
                }), 400

        created_by = get_user_email(user_id)
        if not created_by:
            return jsonify({"error": "User not found or missing email"}), 400

        task_id = get_next_task_id()
        logging.debug(f"Generated task_id: {task_id}")

        task = {
            "task_id": task_id,
            "title": title,
            "description": description,
            "URL": url,
            "timeline": timeline,
            "share_to": share_to,
            "status": "OPEN",
            "created_by": created_by  
        }

        logging.debug(f"Updating user {user_id} with task: {task}")

        #$push operator is used to add an element to an array. 
        result = tasks_collection.update_one(
            {"user_id": user_id},
            {"$push": {"tasks": task}},
            upsert=True
        )

        if result.modified_count == 0 and result.upserted_id is None:
            logging.error("No document was modified or created.")
            return jsonify({"error": "Failed to update or insert task"}), 500

        # Add shared tasks to shared_tasks collection
        for email in share_to_normalized:
            shared_user_id = email_to_user_id[email]
            shared_task_entry = {
                "task_owner_id": user_id,
                "task_id": task_id
            }
            shared_tasks_collection.update_one(
                {"shared_user_id": shared_user_id},
                {"$addToSet": {"shared_tasks": shared_task_entry}},
                upsert=True
            )
            logging.debug(f"Added shared task entry for user {shared_user_id}: {shared_task_entry}")

        return jsonify({"message": "Task created successfully", "task_id": task_id}), 201
    
    except Exception as e:
        logging.error(f"Exception occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500
