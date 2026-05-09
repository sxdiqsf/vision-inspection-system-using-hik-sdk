import cv2
import numpy as np


# ---------------------------------------------------
# Detect only circular holes
# ---------------------------------------------------

def detect_holes(image):

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Reduce noise
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Binary inverse threshold
    _, thresh = cv2.threshold(
        blur,
        80,
        255,
        cv2.THRESH_BINARY_INV
    )

    # Morphological cleanup
    kernel = np.ones((3, 3), np.uint8)

    thresh = cv2.morphologyEx(
        thresh,
        cv2.MORPH_OPEN,
        kernel
    )

    contours, _ = cv2.findContours(
        thresh,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    holes = []

    for cnt in contours:

        area = cv2.contourArea(cnt)

        # Remove tiny noise
        if area < 100:
            continue

        perimeter = cv2.arcLength(cnt, True)

        if perimeter == 0:
            continue

        circularity = 4 * np.pi * area / (perimeter * perimeter)

        # Strict circularity check
        if circularity < 0.7:
            continue

        x, y, w, h = cv2.boundingRect(cnt)

        # Width-height similarity check
        aspect_ratio = w / float(h)

        if aspect_ratio < 0.75 or aspect_ratio > 1.25:
            continue

        cx = x + w // 2
        cy = y + h // 2

        holes.append((cx, cy, w, h))

    holes = sorted(holes, key=lambda h: h[0])

    return holes, thresh


# ---------------------------------------------------
# Main processing
# ---------------------------------------------------

def process_image(image):

    output = image.copy()

    holes, thresh = detect_holes(image)

    total_count = len(holes)

    for idx, hole in enumerate(holes):

        cx, cy, w, h = hole

        radius = max(w, h) // 2

        # Draw circle
        cv2.circle(
            output,
            (cx, cy),
            radius,
            (0, 255, 0),
            2
        )

        # Center point
        cv2.circle(
            output,
            (cx, cy),
            3,
            (255, 255, 0),
            -1
        )

        # Label
        cv2.putText(
            output,
            f"{idx + 1}",
            (cx - 10, cy - radius - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )

    # Final count
    cv2.putText(
        output,
        f"HOLES = {total_count}",
        (30, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2,
        (255, 0, 0),
        3
    )

    return output, thresh


# ---------------------------------------------------
# TEST
# ---------------------------------------------------

img = cv2.imread("341.bmp")

result, thresh = process_image(img)

cv2.imshow("RESULT", result)
cv2.imshow("THRESH", thresh)

cv2.waitKey(0)
cv2.destroyAllWindows()










# import cv2
# import numpy as np


# # ---------------------------------------------------
# # Detect holes
# # ---------------------------------------------------

# # def detect_holes(image):

# #     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# #     # Blur reduces sensor noise
# #     blur = cv2.GaussianBlur(gray, (5, 5), 0)

# #     # Binary inverse threshold
# #     _, thresh = cv2.threshold(
# #         blur,
# #         80,
# #         255,
# #         cv2.THRESH_BINARY_INV
# #     )

# #     # Morph cleanup
# #     kernel = np.ones((3, 3), np.uint8)
# #     thresh = cv2.morphologyEx(
# #         thresh,
# #         cv2.MORPH_OPEN,
# #         kernel
# #     )

# #     contours, _ = cv2.findContours(
# #         thresh,
# #         cv2.RETR_EXTERNAL,
# #         cv2.CHAIN_APPROX_SIMPLE
# #     )

# #     holes = []

# #     for cnt in contours:

# #         area = cv2.contourArea(cnt)

# #         # Remove tiny noise
# #         if area < 100:
# #             continue

# #         perimeter = cv2.arcLength(cnt, True)

# #         if perimeter == 0:
# #             continue

# #         circularity = 4 * np.pi * area / (perimeter * perimeter)

# #         # Hole should be roughly circular
# #         if circularity < 0.5:
# #             continue

# #         x, y, w, h = cv2.boundingRect(cnt)

# #         cx = x + w // 2
# #         cy = y + h // 2

# #         holes.append((cx, cy, w, h))

# #     # Sort left to right
# #     holes = sorted(holes, key=lambda h: h[0])

# #     return holes, thresh


# # # ---------------------------------------------------
# # # Detect bar/block beside hole
# # # ---------------------------------------------------

# # def detect_bar(image, hole):

# #     cx, cy, w, h = hole

# #     # ROI to right side of hole
# #     x1 = cx + 10
# #     x2 = cx + 80

# #     y1 = cy - 40
# #     y2 = cy + 40

# #     # Clamp bounds
# #     x1 = max(0, x1)
# #     y1 = max(0, y1)

# #     x2 = min(image.shape[1], x2)
# #     y2 = min(image.shape[0], y2)

# #     roi = image[y1:y2, x1:x2]

# #     if roi.size == 0:
# #         return False

# #     gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

# #     _, thresh = cv2.threshold(
# #         gray,
# #         100,
# #         255,
# #         cv2.THRESH_BINARY_INV
# #     )

# #     contours, _ = cv2.findContours(
# #         thresh,
# #         cv2.RETR_EXTERNAL,
# #         cv2.CHAIN_APPROX_SIMPLE
# #     )

# #     for cnt in contours:

# #         area = cv2.contourArea(cnt)

# #         # Large blob = bar
# #         if area > 300:
# #             return True

# #     return False


# # ---------------------------------------------------
# # Main sequence logic
# # ---------------------------------------------------

# # def process_image(image):

# #     # Copy original
# #     output = image.copy()

# #     holes, thresh = detect_holes(image)

# #     counting_started = False
# #     bar_count = 0
# #     total_count = 0

# #     for idx, hole in enumerate(holes):

# #         cx, cy, w, h = hole

# #         has_bar = detect_bar(image, hole)

# #         # ---------------------------------------------------
# #         # COLORS
# #         # ---------------------------------------------------

# #         color = (0, 255, 0) if has_bar else (0, 0, 255)

# #         label = "BAR" if has_bar else "NO BAR"

# #         # ---------------------------------------------------
# #         # DRAW HOLE
# #         # ---------------------------------------------------

# #         radius = max(w, h) // 2

# #         # Outer circle
# #         cv2.circle(
# #             output,
# #             (cx, cy),
# #             radius,
# #             color,
# #             2
# #         )

# #         # Center point
# #         cv2.circle(
# #             output,
# #             (cx, cy),
# #             3,
# #             (255, 255, 0),
# #             -1
# #         )

# #         # Bounding box
# #         cv2.rectangle(
# #             output,
# #             (cx - w // 2, cy - h // 2),
# #             (cx + w // 2, cy + h // 2),
# #             color,
# #             1
# #         )

# #         # ---------------------------------------------------
# #         # DRAW BAR ROI
# #         # ---------------------------------------------------

# #         x1 = cx + 10
# #         x2 = cx + 80

# #         y1 = cy - 40
# #         y2 = cy + 40

# #         x1 = max(0, x1)
# #         y1 = max(0, y1)

# #         x2 = min(image.shape[1], x2)
# #         y2 = min(image.shape[0], y2)

# #         cv2.rectangle(
# #             output,
# #             (x1, y1),
# #             (x2, y2),
# #             (255, 0, 255),
# #             1
# #         )

# #         # ---------------------------------------------------
# #         # LABEL
# #         # ---------------------------------------------------

# #         cv2.putText(
# #             output,
# #             f"{idx+1}: {label}",
# #             (cx - 40, cy - radius - 10),
# #             cv2.FONT_HERSHEY_SIMPLEX,
# #             0.5,
# #             color,
# #             2
# #         )

# #         # ---------------------------------------------------
# #         # COUNT LOGIC
# #         # ---------------------------------------------------

# #         if has_bar:

# #             bar_count += 1

# #             if not counting_started:
# #                 counting_started = True

# #             elif bar_count == 4:
# #                 break

# #         if counting_started:
# #             total_count += 1

# #     # ---------------------------------------------------
# #     # FINAL COUNT TEXT
# #     # ---------------------------------------------------

# #     cv2.putText(
# #         output,
# #         f"COUNT = {total_count}",
# #         (30, 50),
# #         cv2.FONT_HERSHEY_SIMPLEX,
# #         1.2,
# #         (255, 0, 0),
# #         3
# #     )

# #     # ---------------------------------------------------
# #     # RESIZE OUTPUT
# #     # ---------------------------------------------------

# #     scale = 0.6

# #     output_resized = cv2.resize(
# #         output,
# #         None,
# #         fx=scale,
# #         fy=scale,
# #         interpolation=cv2.INTER_AREA
# #     )

# #     thresh_resized = cv2.resize(
# #         thresh,
# #         None,
# #         fx=scale,
# #         fy=scale,
# #         interpolation=cv2.INTER_AREA
# #     )

# #     return output_resized, thresh_resized


# import cv2
# import numpy as np


# # ---------------------------------------------------
# # Detect holes
# # ---------------------------------------------------

# def detect_holes(image):

#     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

#     # Blur reduces sensor noise
#     blur = cv2.GaussianBlur(gray, (5, 5), 0)

#     # Binary inverse threshold
#     _, thresh = cv2.threshold(
#         blur,
#         80,
#         255,
#         cv2.THRESH_BINARY_INV
#     )

#     # Morph cleanup
#     kernel = np.ones((3, 3), np.uint8)
#     thresh = cv2.morphologyEx(
#         thresh,
#         cv2.MORPH_OPEN,
#         kernel
#     )

#     contours, _ = cv2.findContours(
#         thresh,
#         cv2.RETR_EXTERNAL,
#         cv2.CHAIN_APPROX_SIMPLE
#     )

#     holes = []

#     for cnt in contours:

#         area = cv2.contourArea(cnt)

#         # Remove tiny noise
#         if area < 100:
#             continue

#         perimeter = cv2.arcLength(cnt, True)

#         if perimeter == 0:
#             continue

#         circularity = 4 * np.pi * area / (perimeter * perimeter)

#         # Hole should be roughly circular
#         if circularity < 0.5:
#             continue

#         x, y, w, h = cv2.boundingRect(cnt)

#         cx = x + w // 2
#         cy = y + h // 2

#         holes.append((cx, cy, w, h))

#     # Sort left to right
#     holes = sorted(holes, key=lambda h: h[0])

#     return holes, thresh


# # ---------------------------------------------------
# # Detect bar/block beside hole
# # ---------------------------------------------------

# # def detect_bar(image, hole):

# #     cx, cy, w, h = hole

# #     # ROI to right side of hole
# #     x1 = cx + 10
# #     x2 = cx + 80

# #     y1 = cy - 40
# #     y2 = cy + 40

# #     # Clamp bounds
# #     x1 = max(0, x1)
# #     y1 = max(0, y1)

# #     x2 = min(image.shape[1], x2)
# #     y2 = min(image.shape[0], y2)

# #     roi = image[y1:y2, x1:x2]

# #     if roi.size == 0:
# #         return False

# #     gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

# #     _, thresh = cv2.threshold(
# #         gray,
# #         100,
# #         255,
# #         cv2.THRESH_BINARY_INV
# #     )

# #     contours, _ = cv2.findContours(
# #         thresh,
# #         cv2.RETR_EXTERNAL,
# #         cv2.CHAIN_APPROX_SIMPLE
# #     )

# #     for cnt in contours:

# #         area = cv2.contourArea(cnt)

# #         # Large blob = bar
# #         if area > 300:
# #             return True

# #     return False


# # ---------------------------------------------------
# # Main sequence logic
# # ---------------------------------------------------

# def process_image(image):

#     # Copy original
#     output = image.copy()

#     holes, thresh = detect_holes(image)

#     counting_started = False
#     bar_count = 0
#     total_count = 0

#     for idx, hole in enumerate(holes):

#         cx, cy, w, h = hole

#         has_bar = detect_bar(image, hole)

#         # ---------------------------------------------------
#         # COLORS
#         # ---------------------------------------------------

#         color = (0, 255, 0) if has_bar else (0, 0, 255)

#         label = "BAR" if has_bar else "NO BAR"

#         # ---------------------------------------------------
#         # DRAW HOLE
#         # ---------------------------------------------------

#         radius = max(w, h) // 2

#         # Outer circle
#         cv2.circle(
#             output,
#             (cx, cy),
#             radius,
#             color,
#             2
#         )

#         # Center point
#         cv2.circle(
#             output,
#             (cx, cy),
#             3,
#             (255, 255, 0),
#             -1
#         )

#         # Bounding box
#         cv2.rectangle(
#             output,
#             (cx - w // 2, cy - h // 2),
#             (cx + w // 2, cy + h // 2),
#             color,
#             1
#         )

#         # ---------------------------------------------------
#         # DRAW BAR ROI
#         # ---------------------------------------------------

#         x1 = cx + 10
#         x2 = cx + 80

#         y1 = cy - 40
#         y2 = cy + 40

#         x1 = max(0, x1)
#         y1 = max(0, y1)

#         x2 = min(image.shape[1], x2)
#         y2 = min(image.shape[0], y2)

#         cv2.rectangle(
#             output,
#             (x1, y1),
#             (x2, y2),
#             (255, 0, 255),
#             1
#         )

#         # ---------------------------------------------------
#         # LABEL
#         # ---------------------------------------------------

#         cv2.putText(
#             output,
#             f"{idx+1}: {label}",
#             (cx - 40, cy - radius - 10),
#             cv2.FONT_HERSHEY_SIMPLEX,
#             0.5,
#             color,
#             2
#         )

#         # ---------------------------------------------------
#         # COUNT LOGIC
#         # ---------------------------------------------------

#         if has_bar:

#             bar_count += 1

#             if not counting_started:
#                 counting_started = True

#             elif bar_count == 4:
#                 break

#         if counting_started:
#             total_count += 1

#     # ---------------------------------------------------
#     # FINAL COUNT TEXT
#     # ---------------------------------------------------

#     cv2.putText(
#         output,
#         f"COUNT = {total_count}",
#         (30, 50),
#         cv2.FONT_HERSHEY_SIMPLEX,
#         1.2,
#         (255, 0, 0),
#         3
#     )

#     # ---------------------------------------------------
#     # RESIZE OUTPUT
#     # ---------------------------------------------------

#     scale = 0.6

#     output_resized = cv2.resize(
#         output,
#         None,
#         fx=scale,
#         fy=scale,
#         interpolation=cv2.INTER_AREA
#     )

#     thresh_resized = cv2.resize(
#         thresh,
#         None,
#         fx=scale,
#         fy=scale,
#         interpolation=cv2.INTER_AREA
#     )

#     return output_resized, thresh_resized
# # ---------------------------------------------------
# # Test
# # ---------------------------------------------------

# img = cv2.imread("26.bmp")

# result, thresh = process_image(img)

# cv2.imshow("RESULT", result)
# cv2.imshow("THRESH", thresh)

# cv2.waitKey(0)

# cv2.destroyAllWindows()
