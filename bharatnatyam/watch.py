import cv2
from ultralytics import YOLO
from mp_hand import handmarks
from landmark_converter_and_classification import (
    is_hand_combined,
    landmark_convert_to_list,
    classify_mudra_using_image
)

vid = r"C:\Projects-aditya\ladki.mp4"
person_model_path = r"person_best.pt"

person = YOLO(person_model_path)
cap = cv2.VideoCapture(0)

# ---------------- STATE ----------------
prev_landmarks = {"Left": None, "Right": None}
previous_mediapipe_landmarks = {"Left": None, "Right": None}
missing_count = {"Left": 0, "Right": 0}
margin=40 #pixel
MAX_MISSING = 3
alpha = 0.7

# ---------------- MAIN LOOP ----------------
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    frame=cv2.resize(frame,(1500,800))
    humans = person.predict(source=frame, imgsz=640, conf=0.80)

    for h in humans:
        if h.boxes is None:
            continue

        frame_h, frame_w = h.orig_shape

        for box in h.boxes.xywh:
            xc, yc, bw, bh = box.tolist()

            bw += 0.1 * frame_w
            bh += 0.1 * frame_h

            x1 = max(0, int(xc - bw / 2))
            y1 = max(0, int(yc - bh / 2))
            x2 = min(frame_w, int(xc + bw / 2))
            y2 = min(frame_h, int(yc + bh / 2))

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

            crop = frame[y1:y2, x1:x2]
            if crop.size == 0:
                continue

            result, HAND_CONNECTIONS = handmarks(crop)
            crop_h, crop_w = crop.shape[:2]

            detected_labels = []

            # ---------------- HAND PROCESSING ----------------
            for hand_landmarks, handedness in zip(
                result.hand_landmarks, result.handedness
            ):
                hand_label = handedness[0].category_name
                detected_labels.append(hand_label)

                # Convert to frame coords
                curr_points = [
                    (
                        int(lm.x * crop_w + x1),
                        int(lm.y * crop_h + y1)
                    )
                    for lm in hand_landmarks
                ]

                # -------- SMOOTHING (PIXEL SPACE) --------
                prev_points = prev_landmarks[hand_label]
                if prev_points is None:
                    smoothed_points = curr_points
                else:
                    smoothed_points = [
                        (
                            int(alpha * cx + (1 - alpha) * px),
                            int(alpha * cy + (1 - alpha) * py),
                        )
                        for (cx, cy), (px, py) in zip(curr_points, prev_points)
                    ]

                prev_landmarks[hand_label] = smoothed_points
                missing_count[hand_label] = 0

                # -------- SMOOTHING (MEDIAPIPE SPACE) --------
                curr_mp = landmark_convert_to_list(hand_landmarks)
                prev_mp = previous_mediapipe_landmarks[hand_label]

                if prev_mp is None:
                    smoothed_mp = curr_mp
                else:
                    smoothed_mp = [
                        (
                            alpha * cx + (1 - alpha) * px,
                            alpha * cy + (1 - alpha) * py,
                            alpha * cz + (1 - alpha) * pz,
                        )
                        for (cx, cy, cz), (px, py, pz) in zip(curr_mp, prev_mp)
                    ]

                previous_mediapipe_landmarks[hand_label] = smoothed_mp

                # # -------- DRAW HAND --------
                # for start, end in HAND_CONNECTIONS:
                #     cv2.line(
                #         frame,
                #         smoothed_points[start],
                #         smoothed_points[end],
                #         (0, 255, 0),
                #         2,
                #     )

                # for x, y in smoothed_points:
                #     cv2.circle(frame, (x, y), 4, (0, 0, 255), -1)

                # wx, wy = smoothed_points[0]
                # cv2.putText(
                #     frame,
                #     hand_label,
                #     (wx, wy - 10),
                #     cv2.FONT_HERSHEY_SIMPLEX,
                #     0.6,
                #     (255, 255, 255),
                #     2,
                # )

            # ---------------- HANDLE LOST HANDS ----------------
            for label in ["Left", "Right"]:
                if label not in detected_labels:
                    if prev_landmarks[label] is not None:
                        missing_count[label] += 1
                        if missing_count[label] > MAX_MISSING:
                            prev_landmarks[label] = None
                            previous_mediapipe_landmarks[label] = None
                            missing_count[label] = 0

            # ---------------- MUDRA CLASSIFICATION ----------------
            left_mp = previous_mediapipe_landmarks.get("Left")
            right_mp = previous_mediapipe_landmarks.get("Right")

            combined = False
            if left_mp is not None and right_mp is not None:
                combined,distance = is_hand_combined(left_mp, right_mp)

            # -------- TWO HAND MUDRA --------
            if combined:
                full_landmark = [left_mp, right_mp]

                xcord = (
                    [p[0] for p in prev_landmarks["Left"]]
                    + [p[0] for p in prev_landmarks["Right"]]
                )
                ycord = (
                    [p[1] for p in prev_landmarks["Left"]]
                    + [p[1] for p in prev_landmarks["Right"]]
                )

                lx, hx = max(0, min(xcord) - margin), max(xcord) + margin
                ly, hy = max(0, min(ycord) - margin), max(ycord) + margin
                crop_img=frame[ly:hy,lx:hx]
                label, conf = classify_mudra_using_image(crop_img)
                if conf>=0.5:
                    cv2.rectangle(frame, (lx, ly), (hx, hy), (0, 0, 0), 2)
                    cv2.putText(
                        frame,
                        f"{label} {conf:.2f} {distance}",
                        (lx, ly - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 255, 255),
                        2,
                    )

            # -------- SINGLE HAND MUDRA --------
            elif not combined:
                for side in ["Left", "Right"]:
                    if prev_landmarks[side] and previous_mediapipe_landmarks[side]:
                        xcord = [p[0] for p in prev_landmarks[side]]
                        ycord = [p[1] for p in prev_landmarks[side]]

                        lx, hx = max(0, min(xcord) - margin), max(xcord) + margin
                        ly, hy = max(0, min(ycord) - margin), max(ycord) + margin
                        #print(frame.shape,ly,hy,lx,hx)
                        crop_img=frame[ly:hy,lx:hx]
                        label, conf = classify_mudra_using_image(crop_img)
                        if conf>=0.5:
                            cv2.rectangle(frame, (lx, ly), (hx, hy), (0, 0, 0), 2)
                            cv2.putText(
                                frame,
                                f"{label} {conf:.2f}",
                                (lx, ly - 10),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.6,
                                (255, 255, 255),
                                2,
                            )

    cv2.imshow("Video Frame", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
