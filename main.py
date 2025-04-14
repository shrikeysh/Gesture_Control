import cv2
import mediapipe as mp
import pyautogui
import tkinter as tk
from tkinter import ttk
import json
import threading
from PIL import Image, ImageTk
import time

GESTURES = {
    "thumbs_up": {
        "detect": lambda landmarks: is_thumb_up(landmarks),
        "action": "volumeup"
    },
    "thumbs_down": {
        "detect": lambda landmarks: is_thumb_down(landmarks),
        "action": "volumedown"
    },
    "palm": {
        "detect": lambda landmarks: is_palm(landmarks),
        "action": "playpause"
    },
    "pointing_index": {
        "detect": lambda landmarks: is_pointing_index(landmarks),
        "action": "next"
    },
    "victory": {  # Add the victory gesture
        "detect": lambda landmarks: is_victory(landmarks),
        "action": "home"
    },
}

def is_thumb_up(landmarks):
    thumb_tip = landmarks.landmark[4]
    thumb_base = landmarks.landmark[3]
    index_tip = landmarks.landmark[8]

    # Ensure thumb is above its base and other fingers are not extended
    is_up = thumb_tip.y < thumb_base.y
    is_other_fingers_folded = all(
        landmarks.landmark[finger_tip_idx].y > landmarks.landmark[finger_tip_idx - 2].y
        for finger_tip_idx in [8, 12, 16, 20]
    )
    print(f"Thumbs Up Detected: {is_up and is_other_fingers_folded}")
    return is_up and is_other_fingers_folded

def is_thumb_down(landmarks):
    thumb_tip = landmarks.landmark[4]
    thumb_base = landmarks.landmark[3]
    index_tip = landmarks.landmark[8]

    # Ensure thumb is below its base and other fingers are not extended
    is_down = thumb_tip.y > thumb_base.y
    is_other_fingers_folded = all(
        landmarks.landmark[finger_tip_idx].y > landmarks.landmark[finger_tip_idx - 2].y
        for finger_tip_idx in [8, 12, 16, 20]
    )
    print(f"Thumbs Down Detected: {is_down and is_other_fingers_folded}")
    return is_down and is_other_fingers_folded

def is_palm(landmarks):
    fingers = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky tips
    extended_fingers = 0

    for finger_tip_idx in fingers:
        finger_tip = landmarks.landmark[finger_tip_idx]
        lower_joint = landmarks.landmark[finger_tip_idx - 2]

        if finger_tip.y < lower_joint.y:  # Higher y-coordinate means upward
            extended_fingers += 1

    print(f"Palm Detected: {extended_fingers == 5}")
    return extended_fingers == 5

def is_pointing_index(landmarks):
    index_tip = landmarks.landmark[8]
    index_base = landmarks.landmark[6]
    folded = True

    for finger_tip_idx in [12, 16, 20]:  # Middle, Ring, Pinky tips
        finger_tip = landmarks.landmark[finger_tip_idx]
        lower_joint = landmarks.landmark[finger_tip_idx - 2]

        if finger_tip.y < lower_joint.y:  # If any other finger is extended
            folded = False
            break

    pointing = index_tip.y < index_base.y and folded
    print(f"Pointing Index Detected: {pointing}")
    return pointing

def is_victory(landmarks):
    index_tip = landmarks.landmark[8]
    index_base = landmarks.landmark[6]
    middle_tip = landmarks.landmark[12]
    middle_base = landmarks.landmark[10]

    # Check if index and middle fingers are extended
    index_extended = index_tip.y < index_base.y
    middle_extended = middle_tip.y < middle_base.y

    # Check if other fingers are folded
    other_fingers_folded = all(
        landmarks.landmark[finger_tip_idx].y > landmarks.landmark[finger_tip_idx - 2].y
        for finger_tip_idx in [16, 20]  # Ring and Pinky fingers
    )

    victory_detected = index_extended and middle_extended and other_fingers_folded
    print(f"Victory Detected: {victory_detected}")
    return victory_detected

class GestureControlUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gesture Control System")
        self.geometry("1000x600")
        self.config = {}
        self.config_lock = threading.Lock()

        self.create_widgets()
        self.start_video_thread()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.load_config()

    def create_widgets(self):
        config_frame = ttk.LabelFrame(self, text="Configuration")
        config_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        ttk.Label(config_frame, text="Gesture:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.gesture_var = tk.StringVar()
        gesture_menu = ttk.Combobox(config_frame, textvariable=self.gesture_var, values=list(GESTURES.keys()), state="readonly")
        gesture_menu.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(config_frame, text="Action:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.action_var = tk.StringVar()
        action_menu = ttk.Combobox(config_frame, textvariable=self.action_var, values=["home", "volumeup", "volumedown", "playpause", "next", "previous"], state="readonly")
        action_menu.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(config_frame, text="Add Mapping", command=self.add_mapping).grid(row=2, column=0, columnspan=2, pady=10)

        self.mappings_list = tk.Listbox(config_frame)
        self.mappings_list.grid(row=3, column=0, columnspan=2, pady=10)

        btn_frame = ttk.Frame(config_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)

        ttk.Button(btn_frame, text="Save Settings", command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Load Settings", command=self.load_config).pack(side=tk.RIGHT, padx=5)

        self.status_label = ttk.Label(config_frame, text="Ready")
        self.status_label.grid(row=5, column=0, columnspan=2, pady=5)

        self.video_label = ttk.Label(self)
        self.video_label.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def add_mapping(self):
        gesture = self.gesture_var.get()
        action = self.action_var.get()
        if gesture and action and gesture in GESTURES:
            with self.config_lock:
                self.config[gesture] = action
            self.mappings_list.insert(tk.END, f"{gesture} → {action}")

    def save_config(self):
        try:
            with open("config.json", "w") as f:
                json.dump(self.config, f, indent=4)
            self.status_label.config(text="Settings saved!", foreground="green")
        except Exception as e:
            self.status_label.config(text=f"Save failed: {str(e)}", foreground="red")

    def load_config(self):
        try:
            with open("config.json", "r") as f:
                self.config = json.load(f)
            self.mappings_list.delete(0, tk.END)
            for gesture, action in self.config.items():
                if gesture not in GESTURES:
                    print(f"[DEBUG] Skipping undefined gesture: {gesture}")
                    continue
                self.mappings_list.insert(tk.END, f"{gesture} → {action}")
            self.status_label.config(text="Settings loaded!", foreground="green")
        except (FileNotFoundError, json.JSONDecodeError):
            self.status_label.config(text="Load failed: No valid config file found.", foreground="red")

    def start_video_thread(self):
        self.video_thread = VideoThread(self)
        self.video_thread.start()

    def on_closing(self):
        self.video_thread.running = False
        self.video_thread.join()
        cv2.destroyAllWindows()  # Ensure all OpenCV windows are closed
        self.destroy()

class VideoThread(threading.Thread):
    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.running = True
        self.hands = mp.solutions.hands.Hands(
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.last_action_time = time.time()
        self.action_cooldown = 2

    def run(self):
        try:
            cap = cv2.VideoCapture(0)
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    print("[DEBUG] Camera feed not available.")
                    continue

                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(rgb_frame)

                if results.multi_hand_landmarks:
                    current_time = time.time()
                    if (current_time - self.last_action_time) > self.action_cooldown:
                        with self.ui.config_lock:
                            current_config = self.ui.config.copy()

                        for landmarks in results.multi_hand_landmarks:
                            if not hasattr(landmarks, 'landmark') or len(landmarks.landmark) < 21:
                                print("[DEBUG] Invalid landmarks detected.")
                                continue
                            for gesture, action in current_config.items():
                                try:
                                    if gesture not in GESTURES:
                                        print(f"[DEBUG] Undefined gesture: {gesture}")
                                        continue
                                    if GESTURES[gesture]["detect"](landmarks):
                                        print(f"[DEBUG] Gesture detected: {gesture}, Action: {action}")
                                        threading.Thread(target=self.handle_action, args=(action,)).start()
                                        self.last_action_time = current_time
                                        break
                                except Exception as e:
                                    print(f"[DEBUG] Error detecting gesture '{gesture}': {str(e)}")

                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.ui.video_label.configure(image=imgtk)
                self.ui.video_label.imgtk = imgtk

            cap.release()
        except Exception as e:
            print(f"[DEBUG] Exception in video thread: {str(e)}")

    def handle_action(self, action):
        try:
            print(f"Executing Action: {action}")
            if action == "home":
                pyautogui.hotkey('win', 'd')
            elif action == "playpause":
                pyautogui.press("playpause")
            elif action == "next":
                pyautogui.press("nexttrack")
            elif action == "previous":
                pyautogui.press("prevtrack")
            elif action in ["volumeup", "volumedown"]:
                pyautogui.press(action)
        except Exception as e:
            print(f"Action Error: {str(e)}")

if __name__ == "__main__":
    app = GestureControlUI()
    app.mainloop()