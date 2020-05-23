from flask import Flask, jsonify, request, render_template, send_from_directory
from flask import Response
import json, os, time
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

door1 = 7  # GPIO4
door2 = 37 # GPIO26

relay1 = 12 # GPIO18
relay2 = 16 # GPIO23
relay3 = 18 # GPIO24
relay4 = 22 # GPIO25

def setupgpio():
    GPIO.setmode(GPIO.BOARD)       # use PHYSICAL GPIO Numbering
    GPIO.setup(door1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(door2, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    GPIO.setup(relay1, GPIO.OUT)
    GPIO.output(relay1, GPIO.LOW)  # default LOW (off)

def loop(socketio):
    setupgpio()
    while True:
        status1 = False
        status2 = False
        if (GPIO.input(door1) == GPIO.LOW):
            log.debug("door1 closed")
        else:
            log.debug("door1 open")
            status1 = True
        if (GPIO.input(door2) == GPIO.LOW):
            log.debug("door2 closed")
        else:
            log.debug("door2 open")
            status2 = True
        socketio.emit('status', {'door1' : status1, 'door2' : status2 }, namespace='/status', broadcast=True)
        time.sleep(1)                   # Wait for 1 second



# routes
@app.route('/')
def index():
    if (GPIO.input(door1) == GPIO.LOW):
        door1buttonimage = '/static/open.jpg';
    else:
        door1buttonimage = '/static/close.jpg';
    if (GPIO.input(door2) == GPIO.LOW):
        door2buttonimage = '/static/open.jpg';
    else:
        door2buttonimage = '/static/close.jpg';
    return render_template('index.html', door1buttonimage=door1buttonimage, door2buttonimage=door2buttonimage);

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
    GPIO.output(relay1, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(relay1, GPIO.LOW)

@app.route('/trigger2')
def trigger2():
    if (GPIO.input(door2) == GPIO.LOW ):
        log.debug("opening door 2")
    else:
        log.debug("closing door 2")
    # trigger door
    GPIO.output(relay2, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(relay2, GPIO.LOW)

@app.route('/status')
@socketio.on('connect', namespace='/status')
def connect():
    log.debug("flask client connected")
    return "OK"
@socketio.on('disconnect', namespace='/status')
def test_disconnect():
    print('flask client disconnected')

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
