# ui.py
import tkinter as tk
from tkinter import ttk
import json
import threading
import cv2
import mediapipe as mp
import pyautogui
from PIL import Image, ImageTk

class GestureControlUI(tk.Tk):
    def __init__(self, gestures_config):
        super().__init__()
        self.title("Gesture Configuration Interface")
        self.geometry("1000x600")
        self.gestures_config = gestures_config
        self.active_mappings = {}
        self.setup_ui()
        self.video_thread = None
        self.start_video_capture()
        self.protocol("WM_DELETE_WINDOW", self.cleanup)

    def setup_ui(self):
        # Video display panel
        self.video_panel = ttk.Label(self)
        self.video_panel.pack(side=tk.LEFT, padx=10, pady=10)

        # Configuration panel
        config_frame = ttk.Frame(self)
        config_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Gesture selection
        ttk.Label(config_frame, text="Available Gestures:").pack(anchor=tk.W)
        self.gesture_selector = ttk.Combobox(config_frame, values=list(self.gestures_config.keys()))
        self.gesture_selector.pack(fill=tk.X, padx=5, pady=5)

        # Action selection
        ttk.Label(config_frame, text="System Action:").pack(anchor=tk.W)
        self.action_selector = ttk.Combobox(config_frame, values=["volumeup", "volumedown", "mute", "playpause", "nexttrack"])
        self.action_selector.pack(fill=tk.X, padx=5, pady=5)

        # Mapping controls
        map_button = ttk.Button(config_frame, text="Map Gesture", command=self.add_mapping)
        map_button.pack(pady=10)

        # Current mappings
        ttk.Label(config_frame, text="Active Mappings:").pack(anchor=tk.W)
        self.mappings_list = tk.Listbox(config_frame, height=8)
        self.mappings_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Configuration management
        button_frame = ttk.Frame(config_frame)
        button_frame.pack(fill=tk.X, pady=10)
        ttk.Button(button_frame, text="Save Config", command=self.save_config).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Load Config", command=self.load_config).pack(side=tk.RIGHT)

    def start_video_capture(self):
        self.video_thread = VideoThread(self.update_video_panel, self.handle_gesture_detection)
        self.video_thread.start()

    def update_video_panel(self, frame):
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_panel.imgtk = imgtk
        self.video_panel.configure(image=imgtk)

    def handle_gesture_detection(self, landmarks):
        for gesture, action in self.active_mappings.items():
            if self.gestures_config[gesture]["detect"](landmarks):
                pyautogui.press(action)

    def add_mapping(self):
        gesture = self.gesture_selector.get()
        action = self.action_selector.get()
        if gesture and action:
            self.active_mappings[gesture] = action
            self.mappings_list.insert(tk.END, f"{gesture} → {action}")

    def save_config(self):
        with open("gesture_config.json", "w") as f:
            json.dump(self.active_mappings, f)

    def load_config(self):
        try:
            with open("gesture_config.json", "r") as f:
                self.active_mappings = json.load(f)
                self.mappings_list.delete(0, tk.END)
                for gesture, action in self.active_mappings.items():
                    self.mappings_list.insert(tk.END, f"{gesture} → {action}")
        except FileNotFoundError:
            pass

    def cleanup(self):
        if self.video_thread:
            self.video_thread.running = False
            self.video_thread.join()
        self.destroy()

class VideoThread(threading.Thread):
    def __init__(self, update_callback, detection_callback):
        super().__init__()
        self.update_callback = update_callback
        self.detection_callback = detection_callback
        self.running = True
        self.hands = mp.solutions.hands.Hands(
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )

    def run(self):
        cap = cv2.VideoCapture(0)
        while self.running:
            success, frame = cap.read()
            if not success:
                continue

            # Process frame
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)

            # Detection logic
            if results.multi_hand_landmarks:
                for landmarks in results.multi_hand_landmarks:
                    self.detection_callback(landmarks)

            # Update UI
            self.update_callback(frame)
        cap.release()