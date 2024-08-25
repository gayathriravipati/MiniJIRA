import logging
from pymongo import MongoClient

logging.basicConfig(level=logging.DEBUG)

client = MongoClient('localhost', 27017)
db = client.jira_database
shared_tasks_collection = db.shared_tasks

def setup_shared_tasks_collection():
    # Check if indexes already exist
    indexes = shared_tasks_collection.index_information()

    # Create an index on shared_user_id if it doesn't exist
    if "shared_user_id_index" not in indexes:
        shared_tasks_collection.create_index("shared_user_id", name="shared_user_id_index")
        logging.info("Created index on shared_user_id")

    # Unique compound index - This prevents the same task from being shared multiple times with the same user.
    if "unique_shared_tasks" not in indexes:
        shared_tasks_collection.create_index(
            [("shared_user_id", 1), ("shared_tasks.task_id", 1)],
            unique=True,
            name="unique_shared_tasks"
        )
        logging.info("Created unique compound index on (shared_user_id, task_id)")

def add_shared_task(shared_user_id, task_owner_id, task_id):
    # Check if the user already has an entry
    query = {"shared_user_id": shared_user_id}
    update = {
        "$addToSet": {
            "shared_tasks": {"task_owner_id": task_owner_id, "task_id": task_id}
        }
    }
    result = shared_tasks_collection.update_one(query, update, upsert=True)
    
    if result.upserted_id:
        logging.info(f"Created new entry for user {shared_user_id}")
    elif result.modified_count > 0:
        logging.info(f"Added task {task_id} for user {shared_user_id}")
    else:
        logging.info(f"Task {task_id} already shared with user {shared_user_id}")

if __name__ == "__main__":
    setup_shared_tasks_collection()
    logging.info("Database setup completed.")