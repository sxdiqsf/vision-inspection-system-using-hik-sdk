import cv2
import numpy as np
import os

# =====================================================
# LOAD IMAGE
# =====================================================

IMAGE_PATH = "169.bmp"

img = cv2.imread(IMAGE_PATH)

if img is None:
    print("Image not found")
    exit()

display = img.copy()

# =====================================================
# OUTPUT FOLDER
# =====================================================

SAVE_DIR = "edge_shape_result"

os.makedirs(SAVE_DIR, exist_ok=True)

# =====================================================
# PREPROCESS
# =====================================================

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

_, thresh = cv2.threshold(
    gray,
    120,
    255,
    cv2.THRESH_BINARY
)

# =====================================================
# FIND MAIN CONTOURS
# =====================================================

contours, _ = cv2.findContours(
    thresh,
    cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_SIMPLE
)

result = 0

for cnt in contours:

    area = cv2.contourArea(cnt)

    # Ignore tiny contours
    if area < 10000:
        continue

    # =====================================================
    # APPROX POLYGON
    # =====================================================

    epsilon = 0.01 * cv2.arcLength(cnt, True)

    approx = cv2.approxPolyDP(
        cnt,
        epsilon,
        True
    )

    # Draw contour
    cv2.drawContours(
        display,
        [approx],
        -1,
        (0, 255, 0),
        2
    )

    # =====================================================
    # CHECK SHARP CORNERS
    # =====================================================

    for point in approx:

        px, py = point[0]

        # Draw corner points
        cv2.circle(
            display,
            (px, py),
            8,
            (0, 0, 255),
            -1
        )

    # # =====================================================
    # # LOGIC
    # # =====================================================

    # # More corners = sharper structure
    # if len(approx) > 12:
    #     result = 0
    # else:
    #     result = 1

    # break

    # =====================================================
    # LOGIC
    # =====================================================

    result = 0

    for i in range(len(approx)):

        p1 = approx[i][0]
        p2 = approx[(i + 1) % len(approx)][0]

        x1, y1 = p1
        x2, y2 = p2

        dx = abs(x2 - x1)
        dy = abs(y2 - y1)

        line_length = np.sqrt(dx * dx + dy * dy)

        # -------------------------------------------------
        # Detect LONG vertical straight edge
        # -------------------------------------------------

        if dx < 20 and dy > 120:

            result = 1

            # Draw detected edge
            cv2.line(
                display,
                (x1, y1),
                (x2, y2),
                (255, 0, 255),
                5
            )

            cv2.putText(
                display,
                "STRAIGHT",
                (x1 + 20, y1),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 0, 255),
                2
            )

            print(
                f"Straight Edge Found: "
                f"dx={dx}, dy={dy}, len={line_length:.2f}"
            )

            break

# =====================================================
# DRAW RESULT
# =====================================================

color = (0, 255, 0) if result == 1 else (255, 0, 0)

cv2.putText(
    display,
    f"RESULT = {result}",
    (50, 80),
    cv2.FONT_HERSHEY_SIMPLEX,
    2,
    color,
    4
)

print("RESULT =", result)

# =====================================================
# SAVE
# =====================================================

cv2.imwrite(
    os.path.join(SAVE_DIR, "threshold.png"),
    thresh
)

cv2.imwrite(
    os.path.join(SAVE_DIR, "final.png"),
    display
)

print("\nSaved:")
print("threshold.png")
print("final.png")

# =====================================================
# SHOW
# =====================================================

cv2.imshow("THRESH", thresh)
cv2.imshow("FINAL", display)

cv2.waitKey(0)
cv2.destroyAllWindows()