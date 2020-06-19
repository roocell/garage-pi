# from https://github.com/miguelgrinberg/flask-video-streaming

import io, os
import time
import picamera
from base_camera import BaseCamera


class Camera(BaseCamera):
    @staticmethod
    def frames():
        with picamera.PiCamera() as camera:
            # let camera warm up
            #camera.start_preview()
            time.sleep(2)

            camera.resolution = (int(os.environ['CAMWIDTH']), int(os.environ['CAMHEIGHT']))
            camera.framerate = int(os.environ['FPS'])

            stream = io.BytesIO()

            for _ in camera.capture_continuous(stream, 'jpeg', use_video_port=True):
                # return current frame
                stream.seek(0)
                yield stream.read()

                # reset stream for next frame
                stream.seek(0)
                stream.truncate()
