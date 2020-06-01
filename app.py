#!/usr/bin/python3

# sudo killall app.py; python3 app.py

from flask import Flask, jsonify, request, render_template, send_from_directory
from flask import Response, redirect, url_for
import json, os, time, sys, datetime
from importlib import import_module
import logging
from flask_socketio import SocketIO, emit
import atexit
import RPi.GPIO as GPIO
from threading import Thread
import keys

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

http = "https://"
#async_mode='threading'
async_mode='eventlet'

if async_mode == 'eventlet':
    # we want to use eventlet (otherwise https certfile doens't work on socketio)
    # but we're using a python thread - so we have to monkeypatch
    import eventlet
    eventlet.monkey_patch()

socketio = SocketIO(app, async_mode=async_mode)

# import camera driver
os.environ['CAMERA'] = "opencv"
os.environ['OPENCV_CAMERA_SOURCE'] = "0"
os.environ['FPS'] = "1"
os.environ['RTSPWIDTH'] = "320"
os.environ['RTSPHEIGHT'] = "240"
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"
if os.environ.get('CAMERA'):
    Camera = import_module('camera_' + os.environ['CAMERA']).Camera
else:
    from camera import Camera
# commend to disable RTSP camera
#rtspCamera = Camera()


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
        #log.debug("%s->%s  %s->%s", status['door1'], status1, status['door2'], status2)
        if (status['door1'] != status1 or status['door2'] != status2):
            #log.debug("emitting door status " + str(status))
            socketio.emit('status', status, namespace='/status', broadcast=True)
        status1 = status['door1']
        status2 = status['door2']
        time.sleep(1)                   # Wait for 1 second


@app.route('/')
def index():
    return render_template('index.html');
@app.route('/handle_data', methods=['POST'])
def handle_data():
    key = request.form['key']
    if (key == keys.authkey):
        response = redirect(url_for("door"))
        response.set_cookie('garage-pi-cookie', keys.authcookie)
    else:
        response = "NOK"
    return response

# routes
@app.route('/door')
def door():
    cookie = request.cookies.get('garage-pi-cookie')
    if (cookie == keys.authcookie):
        log.debug("cookie is valid")
        now = datetime.datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        return render_template('door.html', http=http, rtspwidth=os.environ['RTSPWIDTH'], rtspheight=os.environ['RTSPHEIGHT'], datetime=dt_string);
    else:
        log.debug("cookie is NOT valid")
        return redirect(url_for("index"))

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
    now = datetime.datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    return render_template('rtsp.html', datetime=dt_string);
@app.route('/video/<path:filename>')
def video_dir(filename):
    return send_from_directory(app.root_path + '/video/', filename)

def gen(camera):
    """Video streaming generator function."""

    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        # this religuishes the CPU so another route can be processed
        # but it's far from true concurrency
        # https://github.com/miguelgrinberg/Flask-SocketIO/issues/896
        socketio.sleep(0)
@app.route('/video_feed')
def video_feed():
    return Response(gen(rtspCamera),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

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

    socketio.run(app,
        certfile='/home/pi/garage-pi/fullchain.pem', keyfile='/home/pi/garage-pi/privkey.pem',
        debug=True, host='0.0.0.0', port=5010, use_reloader=False)
