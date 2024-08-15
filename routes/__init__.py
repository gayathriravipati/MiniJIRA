from flask import Flask
from routes.add_user import add_user_bp
from routes.index import index_bp

app = Flask(__name__)

app.register_blueprint(add_user_bp)
app.register_blueprint(index_bp)

if __name__ == '__main__':
    app.run(debug=True)
