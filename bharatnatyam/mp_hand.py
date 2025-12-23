import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import matplotlib.pyplot as plt


# Load image

def handmarks(frame):
    HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (5, 9), (9,10), (10,11), (11,12),      # Middle
    (9,13), (13,14), (14,15), (15,16),     # Ring
    (13,17), (17,18), (18,19), (19,20),    # Pinky
    (0,17)                                # Palm base
]
    # image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Create MediaPipe image
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)

    # Hand landmarker options
    options = vision.HandLandmarkerOptions(
        base_options=python.BaseOptions(
            model_asset_path="hand_landmarker.task"
        ),
        num_hands=2
    )

    # Create landmarker
    with vision.HandLandmarker.create_from_options(options) as landmarker:
        result = landmarker.detect(mp_image)
        return result,HAND_CONNECTIONS
if __name__=="__main__":
    im=cv2.imread(r"C:\Projects-aditya\abcs.jpg")
    res,_=handmarks(im)
    for i,j in zip(res.handedness,res.hand_landmarks):
        print(i)
        print(j)
    #     h, w, _ = frame.shape
    #     for hand_landmarks,handedness in zip(result.hand_landmarks,result.handedness):
    #         # Convert normalized landmarks to pixel coords
    #         #print(handedness)
    #         points = []
    #         for lm in hand_landmarks:
    #             x = int(lm.x * w)
    #             y = int(lm.y * h)
    #             points.append((x, y))
            
    #         # Draw connections
    #         for start, end in HAND_CONNECTIONS:
    #             cv2.line(
    #                 frame,
    #                 points[start],
    #                 points[end],
    #                 color=(0, 255, 0),
    #                 thickness=2
    #             )

    #         # Draw keypoints
    #         (text_w, text_h), baseline = cv2.getTextSize(
    #             handedness[0].category_name,
    #             cv2.FONT_HERSHEY_SIMPLEX,
    #             0.6,
    #             2
    #         )
    #         wx,wy=points[0]
    #         cv2.rectangle(
    #             frame,
    #             (wx - 5, wy - text_h - 15),
    #             (wx + text_w + 5, wy - 5),
    #             (0, 0, 0),
    #             -1
    #         )

    #         cv2.putText(
    #             frame,
    #             handedness[0].category_name,
    #             (wx, wy - 10),
    #             cv2.FONT_HERSHEY_SIMPLEX,
    #             0.6,
    #             (255, 255, 255),
    #             2,
    #             cv2.LINE_AA
    #         )
            
            
    # return frame,points

    
