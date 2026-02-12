# Raspberry Pi + USB Webcam Timelapse

This project allows a Raspberry Pi to create a timelapse using a standard USB Webcam, controlled via a Web Interface.

## Setup

1.  **Hardware**:
    *   Raspberry Pi (Zero W or other)
    *   USB Webcam (Full HD recommended)
    *   Sufficient SD Card space for images

2.  **Verify Camera**:
    *   Plug in the camera.
    *   Run `ls /dev/video*`. You should see `/dev/video0`.

3.  **Dependencies**:
    *   Install OpenCV (headless) and Flask:
    ```bash
    pip3 install -r requirements.txt
    ```
    *   *Note for Pi Zero*: If pip fails on OpenCV, try `sudo apt install python3-opencv`.

## Usage

1.  Start the web server:
    ```bash
    python3 app.py
    ```

2.  Open your browser and navigate to:
    `http://<RASPBERRY_PI_IP>:5000`

## Features
- **Live Preview**: Shows the latest captured image.
- **Controls**: Start/Stop the timelapse.
- **Settings**: Adjust Interval and Resolution on the fly.
- **Status**: View total shots taken and errors.

## Storage Note
Images are saved to the `images/` directory. Ensure you have space!
