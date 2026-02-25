import pyautogui
from config import SENSITIVITY

pyautogui.FAILSAFE = False

def move_mouse(dx, dy):
    pyautogui.moveRel(
        dx * SENSITIVITY,
        dy * SENSITIVITY,
        duration=0
    )