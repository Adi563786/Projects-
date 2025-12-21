import cv2
from ultralytics import YOLO
from mp_hand import handmarks

vid = r"video.mp4"
person_model_path = r"person_best.pt"
person = YOLO(person_model_path)
cap = cv2.VideoCapture(vid)

prev_landmarks = {"Left": None, "Right": None}
missing_count = {"Left": 0, "Right": 0}
MAX_MISSING = 3  # persist for up to 3 frames if lost
alpha = 0.7      # smoothing factor
frame_width = 640
frame_height = 480
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.resize(frame, (1800, frame.shape[0]))
    humans = person.predict(source=frame, imgsz=640, conf=0.80)

    for h in humans:
        if h.boxes is None:
            cv2.imshow("Video Frame",frame)
            continue

        l, b = h.orig_shape

        for _, box in enumerate(h.boxes.xywh):
            xc, yc, bw, bh = box.tolist()
            bw += 0.1 * b
            bh += 0.1 * l
            x1 = int(xc - bw / 2)
            y1 = int(yc - bh / 2)
            x2 = int(xc + bw / 2)
            y2 = int(yc + bh / 2)

            # Clamp to image boundaries
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(b, x2)
            y2 = min(l, y2)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color=(0, 0, 255), thickness=2)
            cv2.circle(frame, (int(xc), int(yc)), radius=5, color=(255, 0, 0), thickness=-1)

            crop = frame[y1:y2, x1:x2]
            if crop.size == 0:
                continue

            result, HAND_CONNECTIONS = handmarks(crop)
            crop_h, crop_w = crop.shape[:2]

            detected_labels = []

            for hand_landmarks, handedness in zip(result.hand_landmarks, result.handedness):
                hand_label = handedness[0].category_name
                detected_labels.append(hand_label)

                # Convert landmarks to original frame coordinates
                landmark_points = [(int(lm.x * crop_w + x1), int(lm.y * crop_h + y1)) for lm in hand_landmarks]

                # Smoothing
                prev = prev_landmarks[hand_label]
                if prev is None or len(prev) != len(landmark_points):
                    smoothed = landmark_points
                else:
                    smoothed = [(int(alpha * cx + (1 - alpha) * px),
                                 int(alpha * cy + (1 - alpha) * py))
                                for (cx, cy), (px, py) in zip(landmark_points, prev)]

                prev_landmarks[hand_label] = smoothed
                missing_count[hand_label] = 0  # reset missing counter
                landmark_points = smoothed

                # Draw landmarks and connections
                for start, end in HAND_CONNECTIONS:
                    cv2.line(frame, landmark_points[start], landmark_points[end], color=(0, 255, 0), thickness=2)
                for (x, y) in landmark_points:
                    cv2.circle(frame, (x, y), radius=4, color=(0, 0, 255), thickness=-1)

                # Draw hand label
                (text_w, text_h), _ = cv2.getTextSize(hand_label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                wx, wy = landmark_points[0]
                cv2.rectangle(frame, (wx - 5, wy - text_h - 15), (wx + text_w + 5, wy - 5), (0, 0, 0), -1)
                cv2.putText(frame, hand_label, (wx, wy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            # Handle vanished hands
            for label in ["Left", "Right"]:
                if label not in detected_labels:
                    if prev_landmarks[label] is not None:
                        missing_count[label] += 1
                        if missing_count[label] <= MAX_MISSING:
                            landmark_points = prev_landmarks[label]
                            for start, end in HAND_CONNECTIONS:
                                cv2.line(frame, landmark_points[start], landmark_points[end], color=(0, 255, 0), thickness=2)
                            for (x, y) in landmark_points:
                                cv2.circle(frame, (x, y), radius=4, color=(0, 0, 255), thickness=-1)
                        else:
                            prev_landmarks[label] = None
                            missing_count[label] = 0
            # handle detection of single hand or combined  hand and classification


        cv2.imshow("Video Frame", frame)
        
        # Exit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# Release resources
cap.release()
cv2.destroyAllWindows()