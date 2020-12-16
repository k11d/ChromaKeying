import numpy as np
import cv2


_image = np.ndarray(shape=(1,1,3), dtype=np.uint8)
_image.fill(0)


def rgb2hsv(rgb):
	_image[:,:,0].fill(rgb[0])
	_image[:,:,1].fill(rgb[1])
	_image[:,:,2].fill(rgb[2])
	h = cv2.cvtColor(_image, cv2.COLOR_RGB2HSV)
	return h[0,0].tolist()


def hsv2rgb(hsv):
	_image[:,:,0].fill(hsv[0])
	_image[:,:,1].fill(hsv[1])
	_image[:,:,2].fill(hsv[2])
	rgb = cv2.cvtColor(_image, cv2.COLOR_HSV2RGB)
	return rgb[0,0].tolist()

