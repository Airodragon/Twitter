from numpy import broadcast
from modules import app
from flask_socketio import SocketIO, send
import datetime
from modules.models import User

socketio = SocketIO(app, cors_allowed_origins='*')

for i in range(1, 10):
    for j in range(i + 1, 11):
        if i != j:
            @socketio.on("message", namespace=f'/chat/{i}/{j}')
            def handleMessage(msg):
                send(msg, broadcast=True)

if __name__ == '__main__':
    app.run(debug=True)