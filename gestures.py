import mediapipe as mp

mp_hands = mp.solutions.hands

GESTURES = {
    "thumbs_up": {
        "detect": lambda landmarks: (
            landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].y < 
            landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y
        ),
        "description": "Thumb above index finger"
    },
    "thumbs_down": {
        "detect": lambda landmarks: (
            landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].y > 
            landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP].y
        ),
        "description": "Thumb below pinky"
    },
    "open_palm": {
        "detect": lambda landmarks: all(
            landmarks.landmark[tip].y < 
            landmarks.landmark[mp_hands.HandLandmark.WRIST].y 
            for tip in [mp_hands.HandLandmark.THUMB_TIP, 
                       mp_hands.HandLandmark.INDEX_FINGER_TIP,
                       mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
                       mp_hands.HandLandmark.RING_FINGER_TIP,
                       mp_hands.HandLandmark.PINKY_TIP]
        ),
        "description": "All fingers extended"
    },
    "victory_sign": {
        "detect": lambda landmarks: (
            landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y < 
            landmarks.landmark[mp_hands.HandLandmark.WRIST].y and
            landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y < 
            landmarks.landmark[mp_hands.HandLandmark.WRIST].y and
            landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP].y > 
            landmarks.landmark[mp_hands.HandLandmark.WRIST].y
        ),
        "description": "Index and middle fingers up"
    },
    "pointing": {
        "detect": lambda landmarks: (
            landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y < 
            landmarks.landmark[mp_hands.HandLandmark.WRIST].y and
            landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].y > 
            landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_DIP].y
        ),
        "description": "Index finger extended"
    }
}