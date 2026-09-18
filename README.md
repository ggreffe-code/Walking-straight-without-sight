# SIGHT Senses — Feel the Way, Hear the World 🦯🔊

A wearable device that helps visually impaired individuals detect and avoid obstacles in real time, using a Raspberry Pi, a camera, a LiDAR sensor, spatialized audio feedback, and haptic vibration.

Built as a school project at [EURECOM](https://www.eurecom.fr), presented at the Mines-Télécom / CTI innovation competition.

**Authors:** Charlyse Jobe, Geoffroy Greffe, Justin Avril, Raphaël Partouche

## Overview

More than 2.2 billion people in the world live with visual impairment, facing numerous obstacles in daily life. SIGHT Senses is a compact, wearable device designed to give them an additional "sense": it detects obstacles and shapes in the environment and translates that information into spatialized sound and vibration feedback, allowing the user to feel and hear the world around them.

## How it works

The device combines three sensing/feedback channels running in parallel on a Raspberry Pi 4:

1. **Image processing** (`camera.py`) — uses the Pi Camera 2 and OpenCV to detect blue guiding lines, squares, and crosses via color masking and contour analysis (Hough-style shape detection). Each detected shape is mapped to a stereo position.
2. **Sound processing** (`camera.py`, via Pydub) — plays a distinct sound for each detected shape (line / square / cross), spatialized through inter-channel time delay and volume balancing so the user can tell where the obstacle is relative to them.
3. **Distance sensing & haptic feedback** (`lidar.py`) — reads distance measurements from a TF-Luna LiDAR sensor over serial and drives a haptic motor (via `RPi.GPIO` PWM) with vibration intensity and rhythm that scale with obstacle proximity (continuous vibration when close, pulsed vibration when very close, no vibration when clear).

Both scripts run concurrently via `run.sh`.

## Hardware

| Component | Role |
|---|---|
| Raspberry Pi 4 | Main compute unit |
| Pi Camera 2 | Shape/obstacle detection |
| LiDAR TF-Luna | Distance measurement |
| Haptic sensor (HALJIA 1027) | Vibration feedback |
| Earphones | Spatialized audio feedback |
| Rechargeable battery | Portability |
| 3D-printed enclosure (9.0 × 6.2 cm) | Wearable housing, designed with battery thermal optimization in mind |

## Software stack

- **Language:** Python 3
- **Image processing:** OpenCV (`cv2`), NumPy
- **Camera:** `picamera2`
- **Audio:** Pydub
- **Sensors / GPIO:** `pyserial`, `RPi.GPIO`

## Repository structure

```
.
├── camera.py   # Image detection + spatialized sound feedback
├── lidar.py    # Distance measurement + haptic feedback
└── run.sh      # Launches both scripts in parallel
```

## Getting started

This project is designed to run on a Raspberry Pi 4 with the camera and LiDAR sensor wired up (LiDAR on `/dev/serial0`, haptic motor on GPIO pin 27).

1. Install the dependencies:
   ```bash
   pip install opencv-python numpy picamera2 pyserial RPi.GPIO pydub
   ```
2. Place `camera.py`, `lidar.py`, and `run.sh` in the same directory, along with the sound assets (`line.mp3`, `cross.mp3`, `square.mp3`, `fence.mp3`) and update the file paths in `camera.py` to match your setup.
3. Run:
   ```bash
   bash run.sh
   ```
4. Stop the programs with `Ctrl+C` / by killing the processes.

## Status & possible improvements

This was built as a proof of concept for a school project. Possible next steps include making sound/asset paths configurable, adding more obstacle shapes, and tuning detection thresholds for different lighting conditions.

## License

Personal / academic project — no license specified yet.
