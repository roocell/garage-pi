#!/usr/bin/python3
from flask import Flask, jsonify, request, render_template, send_from_directory
from flask import Response
import json, os, time, sys
from importlib import import_module
import logging
from flask_socketio import SocketIO, emit
import atexit
import RPi.GPIO as GPIO
from threading import Thread


# create logger
log = logging.getLogger(__file__)
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)

# create flask and socket
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# import camera driver
os.environ['CAMERA'] = "opencv"
os.environ['OPENCV_CAMERA_SOURCE'] = "0"
os.environ['FPS'] = "1"
fps = int(os.environ['FPS'])
if os.environ.get('CAMERA'):
    Camera = import_module('camera_' + os.environ['CAMERA']).Camera
else:
    from camera import Camera


user = "roocell"
password = "garage-pi"

door1 = 7  # GPIO4
door2 = 37 # GPIO26

relay1 = 10 # GPIO15
relay2 = 8 # GPIO14

def setupgpio():
    GPIO.setmode(GPIO.BOARD)       # use PHYSICAL GPIO Numbering
    GPIO.setup(door1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(door2, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # connection is on the NO (normally open) port
    # on the relay
    # this is so when the pi is powered off, the doors
    # won't move
    GPIO.setup(relay1, GPIO.OUT)
    GPIO.output(relay1, GPIO.HIGH)  # default LOW (off)
    GPIO.setup(relay2, GPIO.OUT)
    GPIO.output(relay2, GPIO.HIGH)  # default LOW (off)


def getDoorStatus():
    if (GPIO.input(door1) == GPIO.LOW):
        newstatus1 = False;
    else:
        # ideally we would have another sensor at the open position too
        # but let's just assume it's at least partially open
        newstatus1 = True

    if (GPIO.input(door2) == GPIO.LOW):
        newstatus2 = False;
    else:
        newstatus2 = True
    return {'door1' : newstatus1, 'door2' : newstatus2 }

status1 = False
status2 = False

def loop(socketio):
    global status1
    global status2
    setupgpio()
    while True:
        status = getDoorStatus()
        #log.debug(status)
        # only emit if there's a change
        if (status['door1'] != status1 or status['door2'] != status2):
            socketio.emit('status', status, namespace='/status', broadcast=True)
        status1 = status['door1']
        status2 = status['door2']
        time.sleep(1)                   # Wait for 1 second



# routes
@app.route('/')
def index():
    return render_template('index.html');

# there is no open/close GPIO value
# just set it high to move door.
# it will either close or open depending on the state of the door.
@app.route('/trigger1')
def trigger1():
    if (GPIO.input(door1) == GPIO.LOW ):
        log.debug("opening door 1")
    else:
        log.debug("closing door 1")
    # trigger door
    GPIO.output(relay1, GPIO.LOW)
    time.sleep(0.5)
    GPIO.output(relay1, GPIO.HIGH)
    return "OK"

@app.route('/trigger2')
def trigger2():
    if (GPIO.input(door2) == GPIO.LOW ):
        log.debug("opening door 2")
    else:
        log.debug("closing door 2")

    # trigger door
    GPIO.output(relay2, GPIO.LOW)
    time.sleep(0.5)
    GPIO.output(relay2, GPIO.HIGH)
    return "OK"

@app.route('/status')
@socketio.on('connect', namespace='/status')
def connect():
    global status1
    global status2
    log.debug("flask client connected")
    status = getDoorStatus()
    status1 = status['door1']
    status2 = status['door2']
    # always emit at connect so client can update
    socketio.emit('status', status, namespace='/status', broadcast=True)
    return "OK"
@socketio.on('disconnect', namespace='/status')
def test_disconnect():
    print('flask client disconnected')

@app.route('/rtsp')
def rtsp():
    return render_template('rtsp.html');

#=====================================================
# main
def cleanup():
    log.debug("cleaning up")
    GPIO.cleanup()                      # Release all GPIO

if __name__ == '__main__':
    atexit.register(cleanup)
    log.debug("starting")
    t = Thread(target=loop, args=(socketio,))
    t.start()

    socketio.run(app, debug=True, host='0.0.0.0', use_reloader=False)
