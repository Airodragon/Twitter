from modules import app
from flask_socketio import SocketIO 
import datetime
from modules.models import User

socketio = SocketIO(app,cors_allowed_origins="*")

if __name__ == '__main__':
    app.run(debug=True)