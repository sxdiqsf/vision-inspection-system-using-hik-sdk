import cv2
import numpy as np


# ---------------------------------------------------
# Detect only circular holes
# ---------------------------------------------------

def detect_holes(image):

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    _, thresh = cv2.threshold(
        blur,
        80,
        255,
        cv2.THRESH_BINARY_INV
    )

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

        if area < 100:
            continue

        perimeter = cv2.arcLength(cnt, True)

        if perimeter == 0:
            continue

        circularity = 4 * np.pi * area / (perimeter * perimeter)

        if circularity < 0.7:
            continue

        x, y, w, h = cv2.boundingRect(cnt)

        aspect_ratio = w / float(h)

        if aspect_ratio < 0.75 or aspect_ratio > 1.25:
            continue

        cx = x + w // 2
        cy = y + h // 2

        holes.append((cx, cy, w, h))

    holes = sorted(holes, key=lambda h: h[0])

    return holes, thresh


# ---------------------------------------------------
# Process image
# ---------------------------------------------------

def process_image(image):

    output = image.copy()

    holes, thresh = detect_holes(image)

    cropped_holes = []

    for idx, hole in enumerate(holes):

        cx, cy, w, h = hole

        radius = max(w, h) // 2

        # Draw detection
        cv2.circle(
            output,
            (cx, cy),
            radius,
            (0, 255, 0),
            2
        )

        cv2.putText(
            output,
            f"{idx + 1}",
            (cx - 10, cy - radius - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )

        # ---------------------------------------------------
        # CROP AROUND DETECTED HOLE
        # ---------------------------------------------------

        crop_size = 120

        x1 = max(cx - crop_size, 0)
        y1 = max(cy - crop_size, 0)

        x2 = min(cx + crop_size, image.shape[1])
        y2 = min(cy + crop_size, image.shape[0])

        crop = image[y1:y2, x1:x2]

        cropped_holes.append(crop)

    return output, thresh, cropped_holes


# ---------------------------------------------------
# Load image
# ---------------------------------------------------

IMAGE_PATH = "26.bmp"

image = cv2.imread(IMAGE_PATH)

if image is None:
    print("Image not found")
    exit()


# ---------------------------------------------------
# Run
# ---------------------------------------------------

output, thresh, cropped_holes = process_image(image)


# ---------------------------------------------------
# Show outputs
# ---------------------------------------------------

cv2.imshow("Detected Holes", output)

for i, crop in enumerate(cropped_holes):

    cv2.imshow(f"Cropped Hole {i+1}", crop)

cv2.waitKey(0)
cv2.destroyAllWindows()
# ---------------------------------------------------
# TEST
# ---------------------------------------------------

img = cv2.imread("374.bmp")

result, thresh = process_image(img)

cv2.imshow("RESULT", result)
cv2.imshow("THRESH", thresh)

cv2.waitKey(0)
cv2.destroyAllWindows()
