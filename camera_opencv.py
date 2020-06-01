# from https://github.com/miguelgrinberg/flask-video-streaming

# opencv using FFMPEG underneath - but it's not clear to me how
# to pass all the arguments from ffmpeg.txt (which is the only one that works)
# otherwise, if we use this, the pizero is overwhelmed and can't decode and
# convert the stream properly

import os
import cv2
from base_camera import BaseCamera


class Camera(BaseCamera):
    video_source = "rtsp://roocell:Garagewyze@192.168.1.236/live"
    fps = 10
    def __init__(self):
        #if os.environ.get('OPENCV_CAMERA_SOURCE'):
            #Camera.set_video_source(int(os.environ['OPENCV_CAMERA_SOURCE']))
        if os.environ.get('FPS'):
            Camera.set_fps(int(os.environ['FPS']))
        super(Camera, self).__init__()

    @staticmethod
    def set_video_source(source):
        Camera.video_source = source
    @staticmethod
    def set_fps(fps):
        Camera.fps = fps

    @staticmethod
    def frames():
        # https://docs.opencv.org/3.4/d4/d15/group__videoio__flags__base.html
        #camera = cv2.VideoCapture(Camera.video_source, cv2.CAP_FFMPEG)
        camera = cv2.VideoCapture(Camera.video_source, cv2.CAP_FFMPEG)

        # smaller video allows more FPS and is more stable
        # TODO: work on shrinking frame size
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, int(os.environ['RTSPWIDTH']))
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, int(os.environ['RTSPHEIGHT']))

        # this has an impact on CPU!
        camera.set(cv2.CAP_PROP_FPS, Camera.fps)

        # helps significantly with frame size
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 20]

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
