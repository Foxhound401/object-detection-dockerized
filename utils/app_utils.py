# import the necessary packages
import struct
import six 
import collections
import cv2 
import datetime
import subprocess as sp
import json 
import numpy
import time
from matplotlib import colors
from threading import Thread

class FPS:
    def __init__(self):
        # store the start time, end time, and total number of frames
        # that were examined between the start and end intervals
        self._start = None
        self._end = None
        self._numFrames = 0

    def start(self):
        # start the timer
        self._start = datetime.datetime.now()
        return self
    
    def stop(self):
        # stop the timer
        self._end = datetime.datetime.now()

    def update(self):
        # increment the total number of frames examined during the
        # start and end intervals
        self._numFrames += 1

    def elapsed(self):
        # return the total number of seconds between the start and
        # end interval
        return (self._end - self._start).total_seconds()

    def fps(self):
        # compute the (approximate) frames per second
        return self._numFrames / self.elapsed()

    
class WebcamVideoStream:
    def __init__(self, src=0):
        # initialize the video camera stream and read the first frame
        # from the stream
        self.stream = cv2.VideoCapture(src)
        (self.grabbed, self.frame) = self.stream.read()
        
        # initialize the variable used to indicate if the thread should
        # be stopped
        self.stopped = False

    def start(self):
        # start the thread to read frames from the video stream
        Thread(target=self.update, args=()).start()
        return self
 
    def update(self):
        # keep looping infinitely until the thread is stopped
        while True:
            # if the thread indicator variable is set, stop the thread
            if self.stopped:
                return
                    
            # otherwise, read the next frame from the stream
            (self.grabbed, self.frame) = self.stream.read()
 
    def read(self):
        # return the frame most recently read
        return self.grabbed, self.frame
 
    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True

    def getWidth(self):
        # Get the width of the frames
        return int(self.stream.get(cv2.CAP_PROP_FRAME_WIDTH))

    def getHeight(self):
        # Get the height of the frames
        return int(self.stream.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def getFPS(self):
        # Get the frame rate of the frames
        return int(self.stream.get(cv2.CAP_PROP_FPS))

    def isOpen(self):
        # Get the frame rate of the frames
        return self.stream.isOpened()

    def setFramePosition(self, framePos):
        self.stream.set(cv2.CAP_PROP_POS_FRAMES, framePos)

    def getFramePosition(self):
        return int(self.stream.get(cv2.CAP_PROP_POS_FRAMES))

    def getFrameCount(self):
        return int(self.stream.get(cv2.CAP_PROP_FRAME_COUNT))


class HLSVideoStream:
	def __init__(self, src):
		# initialize the video camera stream and read the first frame
		# from the stream

		# initialize the variable used to indicate if the thread should
		# be stopped
		self.stopped = False

		FFMPEG_BIN = "ffmpeg"

		metadata = {}

		while "streams" not in metadata.keys():
			
			print('ERROR: Could not access stream. Trying again.')

			info = sp.Popen(["ffprobe", 
			"-v", "quiet",
			"-print_format", "json",
			"-show_format",
			"-show_streams", src],
			stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)
			out, err = info.communicate(b"ffprobe -v quiet -print_format json -show_format -show_streams http://52.91.28.88:8080/hls/live.m3u8")

			metadata = json.loads(out.decode('utf-8'))
			time.sleep(5)


		print('SUCCESS: Retrieved stream metadata.')

		self.WIDTH = metadata["streams"][0]["width"]
		self.HEIGHT = metadata["streams"][0]["height"]

		self.pipe = sp.Popen([ FFMPEG_BIN, "-i", src,
				 "-loglevel", "quiet", # no text output
				 "-an",   # disable audio
				 "-f", "image2pipe",
				 "-pix_fmt", "bgr24",
				 "-vcodec", "rawvideo", "-"],
				 stdin = sp.PIPE, stdout = sp.PIPE)
		print('WIDTH: ', self.WIDTH)

		raw_image = self.pipe.stdout.read(self.WIDTH*self.HEIGHT*3) # read 432*240*3 bytes (= 1 frame)
		self.frame =  numpy.fromstring(raw_image, dtype='uint8').reshape((self.HEIGHT,self.WIDTH,3))
		self.grabbed = self.frame is not None


	def start(self):
		# start the thread to read frames from the video stream
		Thread(target=self.update, args=()).start()
		return self

	def update(self):
		# keep looping infinitely until the thread is stopped
		# if the thread indicator variable is set, stop the thread

		while True:
			if self.stopped:
				return

			raw_image = self.pipe.stdout.read(self.WIDTH*self.HEIGHT*3) # read 432*240*3 bytes (= 1 frame)
			self.frame =  numpy.fromstring(raw_image, dtype='uint8').reshape((self.HEIGHT,self.WIDTH,3))
			self.grabbed = self.frame is not None

	def read(self):
		# return the frame most recently read
		return self.frame

	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True
