# from https://github.com/miguelgrinberg/flask-video-streaming

# opencv using FFMPEG underneath - but it's not clear to me how
# to pass all the arguments from ffmpeg.txt (which is the only one that works)
# otherwise, if we use this, the pizero is overwhelmed and can't decode and
# convert the stream properly

import os
import picamera
import cv2
from base_camera import BaseCamera


class Camera(BaseCamera):
    video_source = "http://127.0.0.1:5011/video_feed"
    def __init__(self):
        super(Camera, self).__init__()

    @staticmethod
    def frames():
        # https://docs.opencv.org/3.4/d4/d15/group__videoio__flags__base.html
        camera = cv2.VideoCapture(Camera.video_source)
        #camera = cv2.VideoCapture(Camera.video_source, cv2.CAP_FFMPEG)

        # smaller video allows more FPS and is more stable
        # TODO: work on shrinking frame size
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, int(os.environ['CAMWIDTH']))
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, int(os.environ['CAMHEIGHT']))

        # this has an impact on CPU!
        camera.set(cv2.CAP_PROP_FPS, int(os.environ['FPS']))

        # helps significantly with frame size
        #encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 20]

        if not camera.isOpened():
            raise RuntimeError('Could not start camera.')

        while True:
            # read current frame
            success, img = camera.read()
            if not success:
                print("error reading camera")
                break
            else:
                # encode as a jpeg image and return it
                yield cv2.imencode('.jpg', img)[1].tobytes()
