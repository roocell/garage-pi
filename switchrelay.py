#!/usr/bin/python3
import RPi.GPIO as GPIO
import time

door1 = 7  # GPIO4
door2 = 37 # GPIO26

relay1 = 12 # GPIO18
relay2 = 16 # GPIO23
relay3 = 18 # GPIO24
relay4 = 22 # GPIO25

def setup():
    GPIO.setmode(GPIO.BOARD)       # use PHYSICAL GPIO Numbering
    GPIO.setup(door1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(door2, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    GPIO.setup(relay1, GPIO.OUT)
    GPIO.output(relay1, GPIO.LOW)  # default LOW (off)

def loop():
    while True:
        if (GPIO.input(door1) == GPIO.LOW and GPIO.input(door2) == GPIO.LOW):
            GPIO.output(relay1, GPIO.HIGH)
            print("relay on")
        else:
            GPIO.output(relay1, GPIO.LOW)
            print("relay off")
        time.sleep(1)                   # Wait for 1 second

def destroy():
    print("cleaning up")
    GPIO.cleanup()                      # Release all GPIO

if __name__ == '__main__':    # Program entrance
    print ('Program is starting ... \n')
    setup()
    try:
        loop()
    except KeyboardInterrupt:   # Press ctrl-c to end the program.
        destroy()
