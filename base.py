import cv2
import numpy as np


# ---------------------------------------------------
# Detect holes
# ---------------------------------------------------

def detect_holes(image):

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Blur reduces sensor noise
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Binary inverse threshold
    _, thresh = cv2.threshold(
        blur,
        80,
        255,
        cv2.THRESH_BINARY_INV
    )

    # Morph cleanup
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

        # Hole should be roughly circular
        if circularity < 0.5:
            continue

        x, y, w, h = cv2.boundingRect(cnt)

        cx = x + w // 2
        cy = y + h // 2

        holes.append((cx, cy, w, h))

    # Sort left to right
    holes = sorted(holes, key=lambda h: h[0])

    return holes, thresh


# ---------------------------------------------------
# Detect bar/block beside hole
# ---------------------------------------------------

def detect_bar(image, hole):

    cx, cy, w, h = hole

    # ROI to right side of hole
    x1 = cx + 10
    x2 = cx + 80

    y1 = cy - 40
    y2 = cy + 40

    # Clamp bounds
    x1 = max(0, x1)
    y1 = max(0, y1)

    x2 = min(image.shape[1], x2)
    y2 = min(image.shape[0], y2)

    roi = image[y1:y2, x1:x2]

    if roi.size == 0:
        return False

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    _, thresh = cv2.threshold(
        gray,
        100,
        255,
        cv2.THRESH_BINARY_INV
    )

    contours, _ = cv2.findContours(
        thresh,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    for cnt in contours:

        area = cv2.contourArea(cnt)

        # Large blob = bar
        if area > 300:
            return True

    return False


# ---------------------------------------------------
# Main sequence logic
# ---------------------------------------------------

def process_image(image):

    holes, thresh = detect_holes(image)

    counting_started = False
    bar_count = 0
    total_count = 0

    for hole in holes:

        cx, cy, w, h = hole

        has_bar = detect_bar(image, hole)

        # Visualization
        color = (0, 255, 0) if has_bar else (0, 0, 255)

        cv2.circle(image, (cx, cy), 10, color, 2)

        label = "BAR" if has_bar else "NO BAR"

        cv2.putText(
            image,
            label,
            (cx - 20, cy - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            1
        )

        if has_bar:

            bar_count += 1

            if not counting_started:
                counting_started = True

            elif bar_count == 4:
                break

        if counting_started:
            total_count += 1

    cv2.putText(
        image,
        f"COUNT = {total_count}",
        (30, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2,
        (255, 0, 0),
        3
    )

    return image


# ---------------------------------------------------
# Test
# ---------------------------------------------------

img = cv2.imread("26.bmp")

result = process_image(img)

cv2.imshow("RESULT", result)

cv2.waitKey(0)

cv2.destroyAllWindows()