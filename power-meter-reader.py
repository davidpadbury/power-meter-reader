import cv2
import glob
import os
import os.path
import numpy as np


def clear_debug():
    filelist = glob.glob("output/*.jpg")
    for f in filelist:
        os.remove(f)


def write_debug(img, name):
    cv2.imwrite(f"output/{name}.jpg", img)


clear_debug()

original = cv2.imread("examples/2.jpg")
write_debug(original, "original")

originalSize = original.shape[:2]
resizedSize = (int(originalSize[1] * 0.3), int(originalSize[0] * 0.3))
resized = cv2.resize(original, resizedSize)
write_debug(resized, "resized")

gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
write_debug(gray, "gray")

print("finding circles")
circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 20, np.array([]), 100, 43, 40, 70)
print("found circles")

circles = np.uint16(np.around(circles))
for i in circles[0,:]:
    # draw the outer circle
    cv2.circle(resized,(i[0],i[1]),i[2],(0,255,0),2)
    # draw the center of the circle
    cv2.circle(resized,(i[0],i[1]),2,(0,0,255),3)

write_debug(resized, "circles")
