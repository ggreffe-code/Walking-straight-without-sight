import cv2
import numpy as np
from picamera2 import Picamera2
import serial
import time
import RPi.GPIO as GPIO

vibration_pin = 27
GPIO.setmode(GPIO.BCM)  # GPIO Mode (BOARD / BCM)
GPIO.setup(vibration_pin, GPIO.OUT)

def vibrate(intensity, duration=0.5):
    """
    Makes a haptic sensor vibrate with adjustable intensity and duration.

    Args:
        intensity (float): Intensity of the vibration, between 0.0 (no vibration) and 1.0 (maximum vibration).
        duration (float): Duration of the vibration in seconds.
    """
    if not (0.0 <= intensity <= 1.0):
        raise ValueError("Intensity must be between 0.0 and 1.0.")
    
    # Initialize the PWM
    pwm = GPIO.PWM(vibration_pin, 100)  #Frequency of 100 Hz (adjust based on the motor)
    pwm.start(intensity * 100)          #Sets the duty cycle based on the intensity
    
    time.sleep(duration)                #Duration of vibrations
    
    pwm.stop()                          #Stops the PWM

dist1 = 1.35
dist2 = 1.22

def haptic_(distance):
        if dist2 <= distance <= dist1:
            #Continuous vibrations
            vibrate(0.9, duration=1.5)  #Continuous vibration at 90% intensity for 1.5 seconds
            #Pulsed vibrations
        elif distance < dist2:
            for i in range(5):
                vibrate(1.0, duration=0.3)  #Pulsed vibration at 100% intensity for 0.3 seconds
                time.sleep(0.2)
        else:
            #No vibration if the distance is above 1.8 meters
            time.sleep(0.2)


#TFLuna Lidar Setup
ser = serial.Serial("/dev/serial0", 115200, timeout=0)

def read_distance():
    while True:
        counter = ser.in_waiting
        if counter > 8:
            bytes_serial = ser.read(9)
            ser.reset_input_buffer()
            if bytes_serial[0] == 0x59 and bytes_serial[1] == 0x59:
                distance = bytes_serial[2] + bytes_serial[3] * 256
                return distance / 100.0
        time.sleep(0.1)

while True:

    #Initialize result dictionary
    detection_results = {
        "lidar_distance": None
    }

    #Retrieve lidar distance
    lidar_distance = read_distance()
    detection_results["lidar_distance"] = lidar_distance
    
    #Display detections
    print(detection_results)

    haptic_(detection_results["lidar_distance"])
