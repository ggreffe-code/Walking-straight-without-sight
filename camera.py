import cv2
import numpy as np
from picamera2 import Picamera2
import serial
import time
import RPi.GPIO as GPIO
from pydub import AudioSegment
from pydub.playback import play
from pydub.exceptions import CouldntDecodeError

#Initialize the camera
picam2 = Picamera2()
picam2.start()

#Make the sound seems spacial with a delay between the two channels and an intensity gap.
def balance_sound(sound: AudioSegment, x: float):
    if not -1 <= x <= 1:  #Consider the value on one axis (x) placed between -1 and 1
        raise ValueError("x must be between -1 and 1.")

    channels = sound.split_to_mono()
    if len(channels) == 1:  #Handle mono audio
        left_channel = right_channel = channels[0]
    else:
        left_channel, right_channel = channels

    #Adjust the gain
    left_volume = (1 - x) * 10 
    right_volume = (1 + x) * 10

    left_channel = left_channel.apply_gain(left_volume - 15)
    right_channel = right_channel.apply_gain(right_volume - 15)

    #Put the time delay (very exaggerated to make the spatialization clearer).
    max_delay_ms = 100 
    delay_ms = int(abs(x) * max_delay_ms)
    if x > 0:
        left_channel = AudioSegment.silent(duration=delay_ms) + left_channel
    elif x < 0:
        right_channel = AudioSegment.silent(duration=delay_ms) + right_channel

    #Adjust the length of both channel
    max_length = max(len(left_channel), len(right_channel))
    left_channel = left_channel + AudioSegment.silent(duration=max_length - len(left_channel))
    right_channel = right_channel + AudioSegment.silent(duration=max_length - len(right_channel))
    stereo_sound = AudioSegment.from_mono_audiosegments(left_channel, right_channel)

    #Play the sound
    play(stereo_sound)
    time.sleep(0.2)

    return stereo_sound

#Load audio files
sound_line = AudioSegment.from_file("/home/H3XERTY/dosssier_projet/line.mp3")
sound_cross = AudioSegment.from_file("/home/H3XERTY/dosssier_projet/cross.mp3")
sound_square = AudioSegment.from_file("/home/H3XERTY/dosssier_projet/square.mp3")
sound_fence = AudioSegment.from_file("/home/H3XERTY/dosssier_projet/fence.mp3")

#Test if there is no problem at this step with playing a sound
balance_sound(sound_square, -1)

#Detect blue lines by applying a mask
def detect_blue_lines(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)  #Convert image to HSV color space
    lower_blue = np.array([100, 150, 50])  #Define lower range for blue
    upper_blue = np.array([140, 255, 255])  #Define upper range for blue
    blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)  #Apply the blue mask
    blurred_mask = cv2.GaussianBlur(blue_mask, (5, 5), 0) 
    contours, _ = cv2.findContours(blurred_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  #Find contours

    lines = []
    for contour in contours:
        if cv2.contourArea(contour) > 1000:  #Ignore small contours
            x, y, w, h = cv2.boundingRect(contour)  #Get bounding box
            if h > w:  #Check if the contour resembles a line
                lines.append((x, y, x + w, y + h))

    return lines

#Compute the position relative to blue lines
def calculate_position(image, lines):
    if len(lines) < 2:  #Check if there are at least 2 lines
        return None, None, False

    lines = sorted(lines, key=lambda line: line[0])  #Sort lines from left to right
    left_line = lines[0]
    right_line = lines[1]

    # Calculate the center positions of the lines
    left_center_x = (left_line[0] + left_line[2]) // 2
    right_center_x = (right_line[0] + right_line[2]) // 2
    frame_center_x = image.shape[1] // 2

    left_distance = frame_center_x - left_center_x    # |
    right_distance = right_center_x - frame_center_x  # | Distances from the center

    return left_distance, right_distance, True

# Detect squares in white areas
def detect_squares_in_white_area(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)  #Convert image to HSV color space
    lower_white = np.array([0, 0, 200])      # |
    upper_white = np.array([180, 30, 255])   # | Define lower and upper range for white
    mask = cv2.inRange(hsv, lower_white, upper_white)  # Apply the mask for white
    blurred_mask = cv2.GaussianBlur(mask, (7, 7), 0)  # Blur to reduce noise

    contours, _ = cv2.findContours(blurred_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  #Find contours

    squares = []
    for contour in contours:
        #Approximate contour and threshold
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)  
        if len(approx) == 4 and cv2.isContourConvex(approx):  #Check if it's a convex quadrilateral
            x, y, w, h = cv2.boundingRect(approx)  #Get bounding box
            aspect_ratio = float(w) / h  #Check aspect ratio
            if 0.9 <= aspect_ratio <= 1.1:  #Check if it's close to a square
                squares.append((x, y, w, h))

    return mask, squares

#Detect cross
def detect_cross(image):
    #Convert in HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_white = np.array([0, 0, 200])      # |
    upper_white = np.array([180, 30, 255])   # | Define lower and upper range for white

    #Apply a white mask
    white_mask = cv2.inRange(hsv, lower_white, upper_white)

    #Clean the mask
    kernel = np.ones((3, 3), np.uint8)
    clean_mask = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, kernel)

    #Find contours
    contours, _ = cv2.findContours(clean_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cross_centers = []

    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 500:  #Don't takes into account small objects
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True) 

            if len(approx) >= 11:  #A cross has multiple edges
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = float(w) / h

                if 0.8 <= aspect_ratio <= 1.2:  #Check if it's near to a square
                    moments = cv2.moments(contour)
                    if moments["m00"] != 0: 
                        cx = int(moments["m10"] / moments["m00"])
                        cy = int(moments["m01"] / moments["m00"])
                        cross_centers.append((cx, cy))

    cross_detected = len(cross_centers) > 0  #Check if at least one cross is detected
    return cross_centers, cross_detected

#Get the better cross
def get_best_cross(cross_centers, image):
    if not cross_centers:
        return None
    frame_center = (image.shape[1] // 2, image.shape[0] // 2)  #Center of the frame
    best_cross = min(cross_centers, key=lambda center: np.linalg.norm(np.array(center) - np.array(frame_center)))
    return best_cross

#Get the bigger square
def get_best_square(squares):
    if not squares:
        return None
    best_square = max(squares, key=lambda square: square[2] * square[3]) #Max area
    return best_square

#Main
try:
    while True:
        image = picam2.capture_array()  # Capture an image

        #Initialize results dictionary
        detection_results = {
            "blue_lines": {
                "detected": False,
                "single_line_detected": {"left": False, "right": False},
                "left_distance": None,
                "right_distance": None
            },

            "squares": {"detected": False, "coordinates": []},
            "crosses": {"detected": False, "coordinates": []},
        }

        #Lines detection
        blue_lines = detect_blue_lines(image)

        if len(blue_lines) == 1:  # If only one line is detected
            line = blue_lines[0]
            center_x = (line[0] + line[2]) // 2  # Calculate the center of the line
            frame_center_x = image.shape[1] // 2

            if center_x < frame_center_x:
                detection_results["blue_lines"]["single_line_detected"]["left"] = True
                detection_results["blue_lines"]["left_distance"] = frame_center_x - center_x
            else:
                detection_results["blue_lines"]["single_line_detected"]["right"] = True
                detection_results["blue_lines"]["right_distance"] = center_x - frame_center_x

        elif len(blue_lines) >= 2:  # If two or more lines are detected
            left_dist, right_dist, blue_detected = calculate_position(image, blue_lines)
            if blue_detected:
                detection_results["blue_lines"]["detected"] = True
                detection_results["blue_lines"]["left_distance"] = left_dist
                detection_results["blue_lines"]["right_distance"] = right_dist

        #Squares detection
        mask, squares = detect_squares_in_white_area(image)
        best_square = get_best_square(squares)
        if best_square:
            detection_results["squares"] = {
                "detected": True,
                "coordinates": best_square
            }
            x, y, w, h = best_square
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Draw a rectangle around the square

        #Cross detection
        cross_centers, cross_detected = detect_cross(image)
        best_cross = get_best_cross(cross_centers, image)
        if best_cross:
            detection_results["crosses"] = {
                "detected": True,
                "coordinates": best_cross
            }

        #Play sounds based on detection results
        if detection_results["blue_lines"]["single_line_detected"]["left"] == True and detection_results["blue_lines"]["left_distance"] <= 200:
            balance_sound(sound_line, -1)

        if detection_results["blue_lines"]["single_line_detected"]["right"] == True and detection_results["blue_lines"]["right_distance"] <= 200:
            balance_sound(sound_line, 1)

        if detection_results["squares"]["detected"] == True:
            x_squares = detection_results["squares"]["coordinates"][1]
            x_squares -= 275
            x_squares = -x_squares / 275
            balance_sound(sound_square, x_squares)

        if detection_results["crosses"]["detected"] == True:
            x_cross = detection_results["crosses"]["coordinates"][1]
            x_cross -= 275
            x_cross = -x_cross / 275
            balance_sound(sound_cross, x_cross)

finally:
    picam2.stop()
