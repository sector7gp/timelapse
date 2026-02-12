import cv2
import time
import logging
import threading
import os
import subprocess
from datetime import datetime

logger = logging.getLogger("Camera")

class TimelapseController:
    def __init__(self, output_dir="images"):
        self.output_dir = output_dir
        self.interval = 10 * 60 # Default to 10 minutes (in seconds)
        self.is_running = False
        self.preview_mode = False # Flag for Live View
        self.thread = None
        self.lock = threading.Lock()
        
        # Camera Settings
        self.device_index = 0
        self.width = 1920
        self.height = 1080
        self.brightness = 100
        self.contrast = 100
        self.saturation = 100
        self.exposure = 0 # 0 usually means auto or default, depends on camera
        self.white_balance = 4000 # Auto usually, but specific values needed for manual
        self.auto_wb = True
        
        # State
        self.latest_image_path = None
        self.shots_taken = 0
        self.errors = 0

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def start(self):
        with self.lock:
            if self.is_running:
                return
            self.is_running = True
            self.preview_mode = False
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            logger.info("Timelapse started.")

    def stop(self):
        with self.lock:
            self.is_running = False
            self.preview_mode = False
        if self.thread:
            self.thread.join()
            logger.info("Timelapse stopped.")

    def set_settings(self, interval_mins, width, height):
        with self.lock:
            self.interval = int(float(interval_mins) * 60)
            self.width = int(width)
            self.height = int(height)
            logger.info(f"Settings updated: Interval={self.interval/60}m, Res={self.width}x{self.height}")

    def update_image_settings(self, brightness, contrast, saturation, exposure, white_balance, auto_wb):
        with self.lock:
            self.brightness = int(brightness)
            self.contrast = int(contrast)
            self.saturation = int(saturation)
            self.exposure = int(exposure)
            self.white_balance = int(white_balance)
            self.auto_wb = bool(auto_wb)
            logger.info(f"Image settings updated: B={self.brightness} C={self.contrast} S={self.saturation}")

    def _apply_camera_settings(self, cap):
        """Applies current settings to the OpenCV capture object and via v4l2-ctl."""
        # Note: Property IDs vary by backend, but these are standard for V4L2
        try:
            # Standard OpenCV properties
            cap.set(cv2.CAP_PROP_BRIGHTNESS, self.brightness / 100.0 if self.brightness < 1 else self.brightness) 
            cap.set(cv2.CAP_PROP_CONTRAST, self.contrast)
            cap.set(cv2.CAP_PROP_SATURATION, self.saturation)
            
            # White Balance via OpenCV usually works
            if self.auto_wb:
                 cap.set(cv2.CAP_PROP_AUTO_WB, 1)
            else:
                 cap.set(cv2.CAP_PROP_AUTO_WB, 0)
                 cap.set(cv2.CAP_PROP_WB_TEMPERATURE, self.white_balance)

            # Exposure via v4l2-ctl (more reliable on Pi)
            # Try to construct command
            # exposure_auto: 1=Manual, 3=Auto (V4L2 standard)
            # exposure_absolute: The value
            
            # We need the device path, usually /dev/video0. 
            # OpenCV index 0 maps to /dev/video0, 1 to /dev/video1, etc.
            device_path = f"/dev/video{self.device_index}"
            
            cmd = ['v4l2-ctl', '-d', device_path]
            
            if self.exposure == 0:
                # Treat 0 as "Auto Exposure" for simplicity in UI, or just default
                subprocess.run(cmd + ['-c', 'exposure_auto=3'], check=False)
            else:
                # Manual Exposure
                # 1. Turn off Auto
                subprocess.run(cmd + ['-c', 'exposure_auto=1'], check=False)
                
                # 2. Set Absolute Exposure
                # Map -10 to 10 from UI to actual camera range (often 1-5000 or similar)
                # This mapping depends HEAVILY on the camera. 
                # Let's assume a standard webcam might use 100-2000 range.
                # Center (0) -> 156 (default for many webcams)
                # We'll map linearly for now, but user might need to tune.
                # Let's try mapping the UI range (-10 to 10) to a multiplier of a base.
                
                # Actually, let's use the UI value as a logarithmic step or direct mapping?
                # Webcams often have exposure_absolute from 3 to 2047.
                # Let's try a safer mapping: 
                # 0 = 156 (Standard)
                # Each step adds/subtracts significantly.
                
                base_exposure = 156
                # exponential mapping?
                # let's try linear first: 
                # val = base + (slider * 50)
                # -10 -> 156 - 500 = -344 (clamp to 1)
                # 10 -> 156 + 500 = 656
                
                val = max(1, base_exposure + (self.exposure * 50))
                subprocess.run(cmd + ['-c', f'exposure_absolute={val}'], check=False)
                
        except Exception as e:
            logger.warning(f"Failed to apply some settings: {e}")

    def get_stream(self):
        """Generator function for MJPEG stream. Pauses timelapse loop if running."""
        was_running = self.is_running
        if was_running:
            self.stop() # Pause actual timelapse to free camera
        
        cap = cv2.VideoCapture(self.device_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self._apply_camera_settings(cap)
        
        if not cap.isOpened():
            yield b''
            return

        with self.lock:
            self.preview_mode = True

        try:
            while self.preview_mode:
                # Re-apply settings on fly if changed (optimized to check dirty flag would be better, but direct set is safe enough)
                self._apply_camera_settings(cap)
                
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Encode as JPEG
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                time.sleep(0.1) # Limit FPS for preview
        finally:
            cap.release()
            with self.lock:
                self.preview_mode = False
            # Resume if it was running? User usually restarts manually to confirm settings.
            # But let's leave it stopped to avoid confusion.

    def _capture_loop(self):
        cap = cv2.VideoCapture(self.device_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self._apply_camera_settings(cap)
        
        if not cap.isOpened():
            logger.error("Could not open camera.")
            self.is_running = False
            return

        # Warmup
        time.sleep(2)

        while self.is_running:
            start_time = time.time()
            
            # Re-apply settings before shot
            self._apply_camera_settings(cap)

            # Flush buffer
            for _ in range(2):
                cap.grab()
            
            ret, frame = cap.read()
            if ret:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"img_{timestamp}.jpg"
                filepath = os.path.join(self.output_dir, filename)
                
                try:
                    cv2.imwrite(filepath, frame)
                    with self.lock:
                        self.latest_image_path = filename 
                        self.shots_taken += 1
                    logger.info(f"Captured {filename}")
                except Exception as e:
                    logger.error(f"Error saving image: {e}")
                    with self.lock:
                        self.errors += 1
            else:
                logger.error("Failed to capture frame")
                with self.lock:
                    self.errors += 1
            
            # Smart Sleep
            elapsed = time.time() - start_time
            sleep_time = max(0, self.interval - elapsed)
            
            # Break sleep into chunks to allow quicker stopping
            for _ in range(int(sleep_time)):
                if not self.is_running: break
                time.sleep(1)
            # Sleep remainder
            if self.is_running:
                time.sleep(sleep_time - int(sleep_time))
            
        cap.release()
