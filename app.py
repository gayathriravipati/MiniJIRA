from flask import Flask
from routes.add_user import add_user_bp
from routes.index import index_bp
from routes.create_tasks import create_tasks_bp
from routes.edit_tasks import edit_tasks_bp
from routes.setup_db import setup_shared_tasks_collection

app = Flask(__name__)

setup_shared_tasks_collection()

# Register the Blueprints
app.register_blueprint(add_user_bp)
app.register_blueprint(index_bp)
app.register_blueprint(create_tasks_bp)
app.register_blueprint(edit_tasks_bp)

if __name__ == '__main__':
    app.run(debug=True)