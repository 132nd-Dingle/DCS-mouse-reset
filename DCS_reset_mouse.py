import ctypes
import win32api
import win32con
import time
import pygame
import sys
import configparser
import logging
import os  # Import os module to handle file operations

# Define log file path
LOG_FILE = "center_mouse.log"


# Function to initialize logging
def initialize_logging():
    # Remove all handlers associated with the root logger object to reset logging config
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Ensure the log file is removed if it exists to start fresh each run
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    # Initialize logging
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        filemode="w",  # Overwrite the log file each run
    )


# Initialize logging (must be done before importing other modules that configure logging)
initialize_logging()


# Redirect stdout and stderr to the log file
class LogRedirect:
    def __init__(self, level):
        self.level = level

    def write(self, message):
        if message.strip():  # Avoid logging empty messages
            logging.log(self.level, message.strip())

    def flush(self):
        pass  # No-op for compatibility


sys.stdout = LogRedirect(logging.INFO)  # Redirect print statements
sys.stderr = LogRedirect(logging.ERROR)  # Redirect errors

# Load configuration
CONFIG_FILE = "config.ini"
config = configparser.ConfigParser()


def load_config():
    if not config.read(CONFIG_FILE):
        logging.error(f"Configuration file '{CONFIG_FILE}' not found or invalid.")
        sys.exit(1)

    try:
        settings = {
            "device": int(config["Joystick"]["device"].split(';')[0].strip()),
            "button": int(config["Joystick"]["button"].split(';')[0].strip()),
            "center_x": float(config["Mouse"]["center_x"].split(';')[0].strip()),
            "center_y": float(config["Mouse"]["center_y"].split(';')[0].strip()),
        }

        # Validate that center_x and center_y are in the range 0.0 to 1.0
        if not (0.0 <= settings["center_x"] <= 1.0 and 0.0 <= settings["center_y"] <= 1.0):
            raise ValueError("center_x and center_y must be between 0.0 and 1.0.")

        return settings
    except KeyError as e:
        logging.error(f"Missing configuration key: {e}")
        sys.exit(1)
    except ValueError as e:
        logging.error(f"Invalid value in configuration: {e}")
        sys.exit(1)


def log_available_devices():
    try:
        pygame.init()
        pygame.joystick.init()
        joystick_count = pygame.joystick.get_count()

        if joystick_count < 1:
            logging.info("No joysticks detected.")
            return False

        logging.info(f"{joystick_count} joystick(s) detected:")
        devices_info = []
        for i in range(joystick_count):
            joystick = pygame.joystick.Joystick(i)
            joystick.init()
            button_count = joystick.get_numbuttons()
            device_info = {
                "index": i,
                "name": joystick.get_name(),
                "buttons": button_count,
            }
            devices_info.append(device_info)
            logging.info(f"Joystick {i}: {joystick.get_name()} with {button_count} button(s)")

        return devices_info
    except Exception as e:
        logging.error(f"Error initializing or logging joysticks: {e}")
        sys.exit(1)


def validate_config(settings, devices_info):
    device_index = settings["device"]
    button_index = settings["button"]

    if device_index >= len(devices_info):
        logging.error(f"Invalid joystick index in config: {device_index}. Only {len(devices_info)} device(s) detected.")
        sys.exit(1)

    joystick_info = devices_info[device_index]
    if button_index >= joystick_info["buttons"]:
        logging.error(
            f"Invalid button index in config for device {device_index}: {button_index}. This joystick has {joystick_info['buttons']} buttons.")
        sys.exit(1)


def center_mouse(center_x_frac, center_y_frac):
    user32 = ctypes.windll.user32

    screen_width = user32.GetSystemMetrics(win32con.SM_CXSCREEN)
    screen_height = user32.GetSystemMetrics(win32con.SM_CYSCREEN)

    first_x, first_y = 0, 0
    second_x = int(screen_width * center_x_frac)
    second_y = int(screen_height * center_y_frac)

    win32api.SetCursorPos((first_x, first_y))
    print(f"Mouse moved to initial position: ({first_x}, {first_y})")
    time.sleep(0.05)

    win32api.SetCursorPos((second_x, second_y))
    print(f"Mouse moved to second position: ({second_x}, {second_y})")


def main():
    settings = load_config()
    devices_info = log_available_devices()

    if not devices_info:
        logging.info("Exiting: No joysticks available.")
        sys.exit(1)

    validate_config(settings, devices_info)

    pygame.init()
    pygame.joystick.init()

    try:
        joystick = pygame.joystick.Joystick(settings["device"])
        joystick.init()
        logging.info(f"Joystick initialized: {joystick.get_name()}")
        logging.info(f"Monitoring button index: {settings['button']}")

        logging.info("Listening to Events now:")
        while True:
            pygame.event.pump()
            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONUP:
                    if event.button == settings["button"]:
                        log_message = f"Button {event.button} released!"
                        logging.info(log_message)
                        print(log_message)
                        center_mouse(settings["center_x"], settings["center_y"])

                if event.type == pygame.QUIT:
                    log_message = "Quit event received."
                    logging.info(log_message)
                    print(log_message)

            time.sleep(0.1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        pygame.quit()
        logging.info("Pygame exited cleanly.")


if __name__ == "__main__":
    main()
