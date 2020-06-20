#!/usr/bin/python3

# sudo killall picamstream.py; python3 picamstream.py

from flask import Flask, jsonify, request, render_template, send_from_directory
from flask import Response
import os, time, sys, datetime
from importlib import import_module

# create flask and socket
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

# import camera driver
os.environ['CAMERA'] = "pi"
os.environ['FPS'] = "10"
os.environ['CAMWIDTH'] = "320"
os.environ['CAMHEIGHT'] = "280"
if os.environ.get('CAMERA'):
    Camera = import_module('camera_' + os.environ['CAMERA']).Camera
else:
    from camera import Camera

# seems eventlet and monkeypatch is messing up picamera
# if we run HTTP and use threading it will work
#https://github.com/miguelgrinberg/flask-video-streaming/issues/39

@app.route('/')
def index():
    return "OK"

def gen(camera):
    """Video streaming generator function."""

    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
            b'Content-Type:image/jpeg\r\n'
            b'Content-Length: ' + f"{len(frame)}".encode() + b'\r\n'
            b'\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

#=====================================================
# main
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5011, use_reloader=False)
