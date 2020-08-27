#!/usr/bin/python

import io

import cv2
import imutils
import numpy as np
import picamera

# Motion detection sensitivity
min_area = 100


def handle_new_frame(frame, past_frame, min_area):
    (h, w) = frame.shape[:2]
    r = 500 / float(w)
    dim = (500, int(h * r))
    frame = cv2.resize(frame, dim, cv2.INTER_AREA)  # We resize the frame
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # We apply a black & white filter
    gray = cv2.GaussianBlur(gray, (21, 21), 0)  # Then we blur the picture

    # if the first frame is None, initialize it because there is no frame for comparing the current one with a previous one
    if past_frame is None:
        past_frame = gray
        return past_frame

    # check if past_frame and current have the same sizes
    (h_past_frame, w_past_frame) = past_frame.shape[:2]
    (h_current_frame, w_current_frame) = gray.shape[:2]
    if (
        h_past_frame != h_current_frame or w_past_frame != w_current_frame
    ):  # This shouldnt occur but this is error handling
        print(
            "Past frame and current frame do not have the same sizes {0} {1} {2} {3}".format(
                h_past_frame, w_past_frame, h_current_frame, w_current_frame
            )
        )
        return

    # compute the absolute difference between the current frame and first frame
    frame_detla = cv2.absdiff(past_frame, gray)
    # then apply a threshold to remove camera motion and other false positives (like light changes)
    thresh = cv2.threshold(frame_detla, 50, 255, cv2.THRESH_BINARY)[1]
    # dilate the thresholded image to fill in holes, then find contours on thresholded image
    thresh = cv2.dilate(thresh, None, iterations=2)
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if imutils.is_cv2() else cnts[1]

    # loop over the contours
    for c in cnts:
        # if the contour is too small, ignore it
        if cv2.contourArea(c) < min_area:
            continue
        print("Motion detected!")


def run_detection(camera):
    # with picamera.PiCamera() as camera:

    camera.resolution = (640, 480)
    past_frame = None
    print("Starting motion detection")
    try:
        while True:
            stream = io.BytesIO()
            camera.capture(stream, format="jpeg", use_video_port=False, splitter_port=1)
            data = np.fromstring(stream.getvalue(), dtype=np.uint8)
            frame = cv2.imdecode(data, 1)
            if frame is not None:
                past_frame = handle_new_frame(frame, past_frame, min_area)
                # camera.close()
                return True
            else:
                print("No more frame")
    finally:
        print("Exiting")
