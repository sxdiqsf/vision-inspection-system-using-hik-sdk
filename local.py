import cv2
import numpy as np

# =========================================================
# BAR PRESENCE DETECTION
# Logic:
# Bar Exists  -> GO
# Bar Missing -> NO-GO
# =========================================================

# -----------------------------
# LOAD IMAGE
# -----------------------------
image_path = "374.bmp"   # Change image path if needed
img = cv2.imread(image_path)

if img is None:
    print("Image not found")
    exit()

# =========================================================
# FIXED ROI SETTINGS
# =========================================================
# IMPORTANT:
# Adjust these values based on your actual bar location
#
# x = left position
# y = top position
# w = width
# h = height
# =========================================================

x = 470
y = 260
w = 120
h = 80

# Crop ROI
roi = img[y:y+h, x:x+w]

# =========================================================
# PREPROCESSING
# =========================================================

# Convert to grayscale
gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

# Gaussian blur to reduce noise
blur = cv2.GaussianBlur(gray, (5, 5), 0)

# =========================================================
# THRESHOLDING
# =========================================================
# Bright metallic bar becomes white
# Dark background becomes black
# =========================================================

threshold_value = 140

_, thresh = cv2.threshold(
    blur,
    threshold_value,
    255,
    cv2.THRESH_BINARY
)

# =========================================================
# WHITE PIXEL COUNT
# =========================================================

white_pixels = cv2.countNonZero(thresh)

# =========================================================
# DECISION THRESHOLD
# =========================================================
# Tune this value using:
# Good samples
# Bad samples
# =========================================================

pixel_threshold = 2500

if white_pixels > pixel_threshold:
    result = "GO"
    color = (0, 255, 0)
else:
    result = "NO-GO"
    color = (0, 0, 255)

# =========================================================
# DRAW RESULTS
# =========================================================

# Draw ROI rectangle
cv2.rectangle(
    img,
    (x, y),
    (x+w, y+h),
    color,
    2
)

# Put result text
cv2.putText(
    img,
    f"{result} | Pixels: {white_pixels}",
    (30, 50),
    cv2.FONT_HERSHEY_SIMPLEX,
    1,
    color,
    2
)

# =========================================================
# DISPLAY WINDOWS
# =========================================================

cv2.imshow("Original Image", img)
cv2.imshow("ROI", roi)
cv2.imshow("Threshold", thresh)

print("===================================")
print("BAR DETECTION RESULT")
print("===================================")
print("White Pixels :", white_pixels)
print("Result       :", result)

cv2.waitKey(0)
cv2.destroyAllWindows()