import cv2
import numpy as np

# ==========================================
# LOAD IMAGE
# ==========================================

IMAGE_PATH = "374.bmp"

img = cv2.imread(IMAGE_PATH)

if img is None:
    print("Image not found")
    exit()

display = img.copy()

# ==========================================
# GRAYSCALE + BLUR
# ==========================================

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

blur = cv2.GaussianBlur(gray, (5, 5), 0)

# ==========================================
# THRESHOLD DARK HOLES
# ==========================================

# Holes are dark -> inverse threshold

_, thresh = cv2.threshold(
    blur,
    60,            # adjust if needed
    255,
    cv2.THRESH_BINARY_INV
)

# ==========================================
# MORPH CLEANUP
# ==========================================

kernel = np.ones((3, 3), np.uint8)

thresh = cv2.morphologyEx(
    thresh,
    cv2.MORPH_OPEN,
    kernel,
    iterations=1
)

thresh = cv2.morphologyEx(
    thresh,
    cv2.MORPH_CLOSE,
    kernel,
    iterations=2
)

# ==========================================
# FIND CONTOURS
# ==========================================

contours, _ = cv2.findContours(
    thresh,
    cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_SIMPLE
)

hole_count = 0

# ==========================================
# FILTER HOLES
# ==========================================

for cnt in contours:

    area = cv2.contourArea(cnt)

    # Remove tiny noise
    if area < 150:
        continue

    perimeter = cv2.arcLength(cnt, True)

    if perimeter == 0:
        continue

    circularity = 4 * np.pi * area / (perimeter * perimeter)

    # Hole should be reasonably circular
    if circularity < 0.65:
        continue

    # Bounding box
    x, y, w, h = cv2.boundingRect(cnt)

    # Avoid huge background regions
    if w > 200 or h > 200:
        continue

    hole_count += 1

    # Draw result
    cv2.drawContours(display, [cnt], -1, (0, 255, 0), 2)

    cv2.putText(
        display,
        f"Hole {hole_count}",
        (x, y - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 0),
        2
    )

# ==========================================
# SHOW RESULTS
# ==========================================

print("Hole Count:", hole_count)

cv2.imshow("Threshold", thresh)
cv2.imshow("Detected Holes", display)

cv2.waitKey(0)
cv2.destroyAllWindows()