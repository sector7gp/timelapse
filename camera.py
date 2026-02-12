import cv2
import time
import logging
import threading
import os
from datetime import datetime

logger = logging.getLogger("Camera")

class TimelapseController:
    def __init__(self, output_dir="images"):
        self.output_dir = output_dir
        self.interval = 10
        self.is_running = False
        self.thread = None
        self.lock = threading.Lock()
        
        # Camera settings
        self.device_index = 0
        self.width = 1920
        self.height = 1080
        
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
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            logger.info("Timelapse started.")

    def stop(self):
        with self.lock:
            self.is_running = False
        if self.thread:
            self.thread.join()
            logger.info("Timelapse stopped.")

    def set_settings(self, interval, width, height):
        with self.lock:
            self.interval = int(interval)
            self.width = int(width)
            self.height = int(height)
            logger.info(f"Settings updated: Interval={self.interval}s, Res={self.width}x{self.height}")

    def _capture_loop(self):
        cap = cv2.VideoCapture(self.device_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
        if not cap.isOpened():
            logger.error("Could not open camera.")
            self.is_running = False
            return

        # Warmup
        time.sleep(2)

        while self.is_running:
            start_time = time.time()
            
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
                        self.latest_image_path = filename # Store relative path or absolute for serving? Relative is better for Flask static serving if inside static folder, but here we serve via route.
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
            time.sleep(sleep_time)
            
        cap.release()
