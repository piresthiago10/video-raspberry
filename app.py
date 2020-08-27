import threading

import picamera
from models import detection, motion, record, stream

if __name__ == "__main__":

    try:
        camera = picamera.PiCamera()
    except picamera.exc.PiCameraMMALError as e:
        print(e)

    # verifica se há movimentação
    run_detection = detection.run_detection(camera)

    if run_detection == True:

        capture_thread = record.Record(camera)
        capture_thread.start()
        # capture_thread.join()
        print("iniciando stream")
        stream_thread = stream.Stream(camera)
        stream_thread.start()
        # stream_thread.join()

        jobs = []
        jobs.append(capture_thread)
        jobs.append(stream_thread)

        for job in jobs:
            job.join()
