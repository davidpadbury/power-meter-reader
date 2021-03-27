import sys
import cv2
import glob
import os
import os.path
import numpy as np
import sympy as sp
import mpmath as mp
import math

DIALS = [
  #offset, clockwise
  [-10, True],
  [0, False],
  [-2, True],
  [10, False],
  [10, True]
]

def clear_debug():
    filelist = glob.glob("output/*.jpg")
    for f in filelist:
        os.remove(f)

def write_debug(img, name):
    cv2.imwrite(f"output/{name}.jpg", img)

def find_hand_edge(edges):
    for threshold in range (80, 20, -2):
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold = threshold, minLineLength = 30, maxLineGap = 5)

        if lines is not None:
            return lines[0][0]

# turn the edge of a hand into a ray from the point closest to the centre
def generate_hand_ray(center_point, edge):
    center = sp.Point(center_point)
    first = sp.Point(edge[0:2])
    second = sp.Point(edge[2:4])
    first_dist = center.distance(first)
    second_dist = center.distance(second)

    return sp.Ray(first, second) if first_dist < second_dist else sp.Ray(second, first)

def read_dial(config, idx, img):
    offset, clockwise = config
    offset_r = offset * (np.pi / 180)

    height, width = img.shape[:2]
    center = [width / 2, height / 2]
    radius = int(width / 2)
    circle = sp.Circle(sp.Point(center), radius)

    offset_ray = sp.Ray(sp.Point(center), angle=mp.radians(offset))
    offset_img = img.copy()
    origin_point = [ center[0], 0 ]
    offset_point = [
      math.cos(offset_r) * (origin_point[0] - center[0]) - math.sin(offset_r) * (origin_point[1] - center[1]) + center[0],
      math.sin(offset_r) * (origin_point[0] - center[0]) + math.cos(offset_r) * (origin_point[1] - center[1]) + center[1]
    ]
    cv2.line(offset_img, (int(center[0]), int(center[1])), (int(offset_point[0]), int(offset_point[1])), (0, 255, 0), 2)
    write_debug(offset_img, f"dial-{idx}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    blurred = cv2.GaussianBlur(gray, (5,5), 0)
    write_debug(blurred, f"blurred-{idx}")

    edges = cv2.Canny(blurred, 50, 100)
    write_debug(edges, f"edges-{idx}")

    edge = find_hand_edge(edges)

    hand_edge_img = img.copy()
    cv2.line(hand_edge_img, (edge[0], edge[1]), (edge[2], edge[3]), (0, 255, 0), 2)
    write_debug(hand_edge_img, f"hand-edge-{idx}")

    hand_ray = generate_hand_ray(center, edge)
    circle_intersection = hand_ray.intersection(circle)[0]

    cv2.line(img, (int(center[0]), int(center[1])), (int(circle_intersection.x), int(circle_intersection.y)), (0, 0, 255), 2)
    write_debug(img, f"intersection-{idx}")

    angle_r = math.atan2(circle_intersection.y - center[1], circle_intersection.x - center[0]) - math.atan2(origin_point[1] - center[1], origin_point[0] - center[0])
    angle = angle_r * 180 / np.pi
    if angle < 0:
        angle = 360 + angle
    angle_p = angle/360
    if not clockwise:
        angle_p = 1 - angle_p

    return int(10*angle_p)

clear_debug()

filename = sys.argv[1] if len(sys.argv) > 1 else ""

if not os.path.exists(filename):
    print("Usage: python3 power-meter-reader.py <image>")
    exit(1)

original_full = cv2.imread(filename)
original = original_full[300:300+300,96:96+1020]
write_debug(original, "original")

originalSize = original.shape[:2]
resizedSize = (int(originalSize[1] * 1), int(originalSize[0] * 1))
resized = cv2.resize(original, resizedSize)
write_debug(resized, "resized")

gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
write_debug(gray, "gray")

blurred = cv2.GaussianBlur(gray, (5,5), 0)
write_debug(blurred, "blurred")

circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, 1, 80, param1=65, param2=40, minRadius=70, maxRadius=130)

dials = np.uint16(np.around(circles))[0,:]

sorted_dials = sorted(dials, key=lambda dial: dial[0])
result = ""

for idx, dial in enumerate(sorted_dials):
    x,y,radius = dial
    x1 = x - radius - 10 if x > radius - 10 else 0
    y1 = y - radius - 10 if y > radius - 10 else 0
    dial_img = resized[y1:y+radius+10,x1:x+radius+10].copy()
    value = read_dial(DIALS[idx], idx, dial_img)
    result += str(value)
    # draw the outer circle
    cv2.circle(resized,(x,y),radius,(0,255,0),2)
    # draw the center of the circle
    cv2.circle(resized,(x,y),2,(0,0,255),3)

print(result)

write_debug(resized, "circles")
