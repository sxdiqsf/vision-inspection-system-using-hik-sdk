import cv2
import numpy as np
import os

# ---------------------------------------------------
# LOAD IMAGE
# ---------------------------------------------------

img = cv2.imread("374.bmp")

if img is None:
    print("Image not found")
    exit()

display = img.copy()

# ---------------------------------------------------
# OUTPUT
# ---------------------------------------------------

os.makedirs("bar_output", exist_ok=True)

# ---------------------------------------------------
# PREPROCESS
# ---------------------------------------------------

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Bright metal extraction
_, thresh = cv2.threshold(
    gray,
    180,
    255,
    cv2.THRESH_BINARY
)

# Morph cleanup
kernel = np.ones((3, 3), np.uint8)

thresh = cv2.morphologyEx(
    thresh,
    cv2.MORPH_OPEN,
    kernel
)

# ---------------------------------------------------
# FIND CONTOURS
# ---------------------------------------------------

contours, _ = cv2.findContours(
    thresh,
    cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_SIMPLE
)

bar_index = 0

for cnt in contours:

    area = cv2.contourArea(cnt)

    if area < 1000:
        continue

    x, y, w, h = cv2.boundingRect(cnt)

    aspect_ratio = h / float(w)

    # ---------------------------------------------------
    # STRICT BAR FILTER
    # ---------------------------------------------------

    # Tall vertical rectangle
    if (
        h > 120 and
        w > 20 and
        aspect_ratio > 2.0
    ):

        # Ignore giant body regions
        if w > 150:
            continue

        bar_index += 1

        cv2.rectangle(
            display,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            3
        )

        cv2.putText(
            display,
            f"BAR {bar_index}",
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        print(
            f"BAR {bar_index}: "
            f"x={x}, y={y}, w={w}, h={h}"
        )

# ---------------------------------------------------
# SAVE OUTPUT
# ---------------------------------------------------

cv2.imwrite(
    "bar_output/result.png",
    display
)

cv2.imwrite(
    "bar_output/thresh.png",
    thresh
)

print("\nSaved:")
print("bar_output/result.png")
print("bar_output/thresh.png")

# ---------------------------------------------------
# SHOW
# ---------------------------------------------------

cv2.imshow("THRESH", thresh)
cv2.imshow("RESULT", display)

cv2.waitKey(0)
cv2.destroyAllWindows()