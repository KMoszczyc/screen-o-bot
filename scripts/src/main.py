import os
import pyautogui as gui
import time
import datetime as dt
import sys
import mss
import mss.tools
import numpy as np
import cv2
from skimage.metrics import structural_similarity as compare_ssim
from argparse import ArgumentParser
from pathlib import Path

print(os.getcwd())
print(Path(os.getcwd()).parents[0])
print(Path(os.getcwd()).parents[1])
print(str(Path(os.getcwd()).parents[1]) + '/screens')

# Time between pyautogui commands
gui.PAUSE = 0.05

# Counter used for file naming
counter = "0000"

# Sleep time after taking screenshot
time_between_screenshots = 0

# Parameter that dictates, how similar previous screenshot must be in relation to current screen state
comparison_confidence = 0.95

# Parameter that dictates, how comparison confidence of excluded files to current screen state
excluded_comparison_confidence = 0.95

# Default folder for screens
# TODO: some input method instead of hardcoding it
ROOT = str(Path(os.getcwd()).parents[1])
SCREENS_PATH = ROOT + '/screens'

MONITOR_NUM = 1  # 0 - for all monitors, 1 - left monitor, 2 - right monitor
SCREEN_SIZES = [(1920, 1080), (2560, 1440)]  # left and right monitor

# Default folder name, set after invoking create_dated_folder() method
folder_name = ""
previous_frame = []

print('save path', SCREENS_PATH)


def get_screen_bbox(sct):
    """
    Some magic code for dual screen setup, where left monitor is 1920x1080 and right monitor is 2560x1440.
    Left one has 100% scale, right one has 125%, hence why there is magic 56 in code below.

    For monitors with same size and scale, all of it could be simplified to:
        left = mon['left']
        top = mon['top']
        right = mon['left'] + mon['width']
        bottom = mon['top'] + mon['height']
    """
    mon = sct.monitors[MONITOR_NUM]

    # The screen part to capture
    left = -SCREEN_SIZES[MONITOR_NUM - 1][0] if MONITOR_NUM == 1 else mon['left']
    top = mon['top'] - 56 if MONITOR_NUM == 1 else mon['top']
    right = left + mon['width'] if MONITOR_NUM == 0 else left + SCREEN_SIZES[MONITOR_NUM - 1][0]
    bottom = top + mon['height'] if MONITOR_NUM == 0 else top + SCREEN_SIZES[MONITOR_NUM - 1][1]

    return left, top, right, bottom


def create_screens_folder():
    os.umask(0)
    print(SCREENS_PATH)
    if not os.path.exists(SCREENS_PATH):
        print('Create screens dir')
        os.makedirs(SCREENS_PATH, mode=0o777)


def get_main_folder_path():
    main_path = os.path.realpath(__file__).split("\\")
    main_path = main_path[:-2]
    return "\\".join(main_path)


def get_excluded_path():
    excluded_path = get_main_folder_path() + r"\excluded"
    return excluded_path


def list_excluded_files():
    list_temp = [f for f in os.listdir(get_excluded_path())
                 if os.path.isfile(os.path.join(get_excluded_path(), f))]
    list_temp = [get_excluded_path() + "\\" + elem for elem in list_temp]
    return list_temp


# Make list of excluded files constant to improve performance
list_of_excluded_files = list_excluded_files()


def create_dated_folder():
    """
    Creates folder with current date and time in format YYYY-MM-DD hh-mm
    Every screenshot taken during current session is stored inside this folder
    When program is run twice in the same minute, files from later session overwrites
    files from earlier one
    """
    global folder_name
    folder_name = "\\" + dt.datetime.now().strftime("%Y-%m-%d %H.%M")
    try:
        os.makedirs(SCREENS_PATH + folder_name)
        print(SCREENS_PATH + folder_name)
    except FileExistsError:
        pass


def take_screenshot(sct):
    """
    Takes screenshot of the specified screen region
    """
    global previous_frame

    # TODO: check best time_between_screenshots time
    # TODO: implement something to specify screen region instead of hardcoding it
    increment_counter()
    output_path = SCREENS_PATH + folder_name + fr"\screenshot_{counter}.png"
    bbox = get_screen_bbox(sct)

    # Grab the data
    sct_img = sct.grab(bbox)
    previous_frame = cv2.cvtColor(np.array(sct_img), cv2.COLOR_RGB2BGR)
    mss.tools.to_png(sct_img.rgb, sct_img.size, output=output_path)
    time.sleep(time_between_screenshots)

    print('screenshot:', counter, '-', dt.datetime.now().strftime("%H:%M:%S"))


def play_notification_sound():
    # TODO: odd option to turn the sound on/off
    # TODO: check if asynchronous playing is necessary
    # TODO: add volume control
    # winsound.MessageBeep(type=winsound.MB_ICONHAND)
    pass


def increment_counter():
    """
    Increases counter by 1 to not overwrite previous screenshots
    Counter is always 3-digit number in format XXX
    Small numbers have leading zeros
    """
    global counter
    counter = int(counter) + 1
    counter = str(counter).zfill(4)


def sth_excluded_is_on_screen():
    global list_of_excluded_files
    for excluded_elem in list_of_excluded_files:
        try:
            loc = gui.locateOnScreen(excluded_elem, confidence=excluded_comparison_confidence)
            return bool(loc)
        except gui.ImageNotFoundException:
            pass
    return False


def screen_has_changed(sct):
    """
    Checks if current screen state is similar to latest screenshot
    returns true if there is difference between current, and previous screenshot
    meaning - screenshot should be taken, as screen state has changed
    returns false if previous screenshot is the same as current screen state
    """
    while True:
        try:
            bbox = get_screen_bbox(sct)
            current_frame = cv2.cvtColor(np.array(sct.grab(bbox)), cv2.COLOR_RGB2BGR)

            (score, diff) = compare_ssim(current_frame, previous_frame, full=True, multichannel=True)

            return score < comparison_confidence

        except gui.ImageNotFoundException:
            return True
        except IOError:
            time.sleep(0.25)


def check_for_program_termination():
    """
    pyautogui has FAILSAFE method that when set to True throws FailSafeException if cursor
    is put in the upper left corner of the screen
    However, exception is sometimes not thrown
    This method implements same behaviour, but exception throwing is much more reliable
    """
    x, y = gui.position()
    if x == 1919 and y == 1079:
        raise gui.FailSafeException


def main_loop():
    """
    Main program loop
    Stops when mouse is moved to upper left corner of the screen
    """
    with mss.mss() as sct:
        create_screens_folder()
        create_dated_folder()
        take_screenshot(sct)
        print("program works")
        while True:
            time.sleep(0.2)
            try:
                check_for_program_termination()
            except gui.FailSafeException:
                gui.alert(text="Program has been stopped", title="Program terminated")
                exit()
            if screen_has_changed(sct) and not sth_excluded_is_on_screen():
                take_screenshot(sct)
                # play_notification_sound()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('-m', '--monitor_num', default=1, required=False,
                        help="Specify the monitor to be caputured (1: left, 2: right) - default: 1")

    args = parser.parse_args()
    MONITOR_NUM = int(args.monitor_num)

    main_loop()
