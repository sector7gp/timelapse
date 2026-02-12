# Raspberry Pi Webcam Timelapse (Tony's Version)

This project allows a Raspberry Pi to create a timelapse using a standard USB Webcam, controlled via a modern **Navy Blue Web Interface**.

**Repository**: [https://github.com/sector7gp/timelapse](https://github.com/sector7gp/timelapse)

## Features

1.  **USB Webcam Support**: Uses OpenCV to capture high-quality images.
2.  **Web Interface**:
    - **Live View**: Real-time video stream to adjust focus and lighting.
    - **Pro Controls**: Sliders for **Brightness**, **Contrast**, **Saturation**, **Exposure**, and **White Balance**.
    - **Presets**: Toggle between **Full HD (1920x1080)** and **HD (1280x720)**.
    - **Config**: Set interval in **Minutes**.
    - **Status**: Monitor shots taken and errors.
3.  **Background Processing**: Image capture runs in a separate thread.
4.  **Robust Error Handling**: Automatically retries on capture failures.

## Setup

1.  **Hardware**:
    *   Raspberry Pi (Zero W or other)
    *   USB Webcam
    *   Sufficient SD Card space

2.  **Dependencies**:
    *   Install OpenCV (headless) and Flask:
    ```bash
    pip3 install -r requirements.txt
    ```

## Usage

1.  Start the web server:
    ```bash
    python3 app.py
    ```

2.  Open your browser and navigate to:
    `http://<RASPBERRY_PI_IP>:5000`

### Using Live View
1.  Ensure the Timelapse is **STOPPED**.
2.  Click **"Start Live View"**.
3.  Adjust the sliders (Brightness, Contrast, etc.) and see the changes in real-time.
4.  Click **"Close Live View"** when satisfied.
5.  Click **"Start Timelapse"** to begin capturing.

## Storage Note
Images are saved to the `images/` directory. Ensure you have space!
