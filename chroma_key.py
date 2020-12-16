#!/usr/bin/env python3

import cv2
import numpy as np


# TODO (included but not limited to:)
#
## Use HSV colorspace instead of RGB 
# all colors are mapped on the Hue range, whereas in RGB (or BGR) colors are determined by the difference between each channel;
# increaing or decreasing each 3 by the same value doesnt change the color but it's luminance. 
#  
## Refactor MovieStreamKe to have better separation between code:
# - showing preview on screen + handling keyboard/mouse inputs 
# - keeping track of selected colors, computing masks for current frame and applying them.



class LuminanceKey(object):

    def __init__(self):
        self.frame = None
        self.mask = None
        self.tolerance = 18 #T t
        self._target_colors = []
        self._hsv_target_colors = [] 
        self._new_color = 0, 0, 0, 255
        self._target_colors_locations = []
        self.main_window = "Final"
        self.aux_window = "Mask"
        cv2.namedWindow(self.main_window, cv2.WINDOW_GUI_NORMAL)
        cv2.setMouseCallback(self.main_window, self.mouse_callback)
        cv2.namedWindow(self.aux_window, cv2.WINDOW_GUI_NORMAL)
        cv2.setWindowTitle(self.main_window, self.main_window)
        cv2.setWindowTitle(self.aux_window, self.aux_window)

        self._left_btn_held = False
        self._right_btn_held = False
        self._shift_key_held = False

    def __enter__(self):
        return self

    def __exit__(self, e, r, t):
        cv2.destroyAllWindows()

    def clear_target_colors(self):
        self._target_colors_locations.clear()
        self._target_colors.clear()

    def mouse_callback(self, event, x, y, p, trb):
        if self.frame is not None:
            print(event, p)
            if event == 4 and p == 1: # left btn up
                self._left_btn_held = False
            if event == 1 and p == 1: # left btn down 
                self._left_btn_held = True
            if event == 5 and p == 2: # right btn up
                self._right_btn_held = False
            if event == 2 and p == 2: # right btn down
                self._right_btn_held = True

            if event == 0: # mouse move
                if self._left_btn_held:
                    hsv_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2HSV)
                    hsv_pix = [hsv_frame[y,x,0], hsv_frame[y,x,1], hsv_frame[y,x,2]]
                    bgr_pix = [self.frame[y,x,0], self.frame[y,x,1], self.frame[y,x,2]]
                    print(f"BGR: {bgr_pix} <=> HSV: {hsv_pix}")
                    try:
                        self._target_colors.append([self.frame[y,x,0], self.frame[y,x,1], self.frame[y,x,2], 255])
                    except IndexError:
                        return
                    self._target_colors_locations.append([y,x])
            if event == 2: # right btn down
                self._right_btn_held = True

                self._target_colors = [[self.frame[y,x,0], self.frame[y,x,1], self.frame[y,x,2], 255]]
        

    def target_colors_mask(self):

        def _create_mask(r,g,b,tol):
            bmin, gmin, rmin = max(0, b-tol), max(0, g-tol), max(0, r-tol)
            bmax, gmax, rmax = min(255, b+tol), min(255, g+tol), min(255, r+tol)
            blue, green, red = self.frame[:,:,0], self.frame[:,:,1], self.frame[:,:,2]
            mask_high_cut  = (blue <= bmax) & (green <= gmax) & (red <= rmax)
            mask_low_cut = (blue >= bmin) & (green >= gmin) & (red >= rmin)
            return mask_high_cut & mask_low_cut
        
        mask = None
        for b,g,r,_ in self._target_colors:
            if mask is None:
                mask = _create_mask(b, g, r, self.tolerance)
            else:
                mask = mask | _create_mask(b, g, r, self.tolerance)
        return mask


    def swap_colors(self):
        if len(self._target_colors) > 0:
            r2, g2, b2, a = self._new_color
            self.mask = self.target_colors_mask()
            final_mask = np.array(self.frame)
            final_mask[:,:,2].fill(255)
            final_mask[:,:,:4][self.mask] = [r2, g2, b2, a]
            self.mask = final_mask
        if self.mask is not None:
            cv2.imshow(self.aux_window, self.mask)


class ImageAsStream(object):

    def __init__(self, sources=()):
        self.sources = sources
        self.pos = 0
        self.image = None
        self.capture()

    def capture(self):
        if type(self.sources[self.pos]) == str:
            self.image = cv2.imread(self.sources[self.pos])
        elif type(self.src) == np.ndarray:
            self.image = self.src
        else:
            raise RuntimeError(f"Unknown source type : {type(self.src)}")
    
    def isOpened(self):
        return not (self.image is None)

    def read(self):
        return self.isOpened(), self.image

    def release(self):
        self.image = None


class MovieStreamKey(LuminanceKey):
    
    def open_movie_stream(self, src="/dev/video0"):
        if type(src) == ImageAsStream:
            cap = src
        else:
            cap = cv2.VideoCapture(src)
        while cap.isOpened():
            ret, _frame = cap.read()
            if not ret:
                break
            else:
                self.frame = cv2.cvtColor(_frame, cv2.COLOR_BGR2BGRA)
                self.swap_colors()
                cv2.imshow(self.main_window, self.frame)
                k = cv2.waitKey(1)
                if k == 27 or k == ord('^'):
                    break
                elif k == 225:
                    self._shift_key_held = True
                elif k == ord('t'):
                    self.tolerance += 1
                    print(f"Tolerance: {self.tolerance}")
                elif k == ord('z'):
                    self.tolerance -= 1
                    print(f"Tolerance: {self.tolerance}")
                elif k == ord('c'):
                    self.clear_target_colors()
                elif k == ord('p'):
                    self._target_colors.pop()
                else:
                    if k != -1:
                        self._shift_key_held = False
                        print(k)
        cap.release()



_IMAGE_EXTS = ('.jpg', '.png', '.bmp', '.gif')
_MOVIE_EXTS = ('.mp4', '.avi', '.mov', '.webm', '.flv')


if __name__ == '__main__':
    import sys, os
    with MovieStreamKey() as msk:
        if len(sys.argv) > 1:
            for s in sys.argv[1:]:
                if os.path.splitext(s)[1].lower() in _MOVIE_EXTS:
                    msk.open_movie_stream(s)
                elif os.path.splitext(s)[1].lower() in _IMAGE_EXTS:
                    msk.open_movie_stream(ImageAsStream(s))
        else:
            msk.open_movie_stream()

