import subprocess
import os

def check_controls(device_index=0):
    device_path = f"/dev/video{device_index}"
    if not os.path.exists(device_path):
        print(f"Error: Device {device_path} not found.")
        return

    print(f"Checking controls for {device_path}...")
    try:
        result = subprocess.run(['v4l2-ctl', '-d', device_path, '--list-ctrls'], 
                              capture_output=True, text=True, check=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running v4l2-ctl: {e}")
        print(e.stderr)
    except FileNotFoundError:
        print("Error: v4l2-ctl not found. Please install v4l-utils (sudo apt install v4l-utils)")

if __name__ == "__main__":
    check_controls()
