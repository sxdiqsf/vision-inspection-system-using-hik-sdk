import cv2
import numpy as np
import sys

def find_button_crop(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (9, 9), 2)

    circles = cv2.HoughCircles(
        blur,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=100,
        param1=100,
        param2=30,
        minRadius=40,
        maxRadius=300
    )

    if circles is None:
        return None

    circles = np.round(circles[0, :]).astype(int)
    x, y, r = circles[0]

    pad = 10
    r_new = r + pad

    x1 = max(x - r_new, 0)
    y1 = max(y - r_new, 0)
    x2 = min(x + r_new, img.shape[1])
    y2 = min(y + r_new, img.shape[0])

    crop = img[y1:y2, x1:x2]

    if crop.size == 0:
        return None
    
    # Circle center inside cropped image
    cx = x - x1
    cy = y - y1

    # Create mask
    mask = np.zeros(crop.shape[:2], dtype=np.uint8)
    cv2.circle(mask, (cx, cy), r_new, 255, -1)

    # Keep only inside circle
    masked_crop = cv2.bitwise_and(crop, crop, mask=mask)

    # draw debug image
    debug = img.copy()

    # detected circle
    cv2.circle(debug, (x, y), r, (0, 255, 0), 2)

    # center point
    cv2.circle(debug, (x, y), 3, (0, 0, 255), -1)

    # crop rectangle
    cv2.rectangle(debug, (x1, y1), (x2, y2), (255, 0, 0), 2)

    cv2.imshow("Detected Circle + Crop Box", debug)
    cv2.imshow("Cropped Button", crop)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    return masked_crop

def classify_button(img):
    # Resize fixed
    img = cv2.resize(img, (300, 300))

    # Gray
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Denoise
    # gray = cv2.GaussianBlur(gray, (5, 5), 0)

    # Edges
    edges = cv2.Canny(gray, 60, 150)

    # Circular mask (button area only)
    h, w = edges.shape
    Y, X = np.ogrid[:h, :w]
    cx, cy = w // 2, h // 2
    r = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)

    # Use inside button face
    mask = (r < 140).astype(np.uint8) * 255
    masked = cv2.bitwise_and(edges, edges, mask=mask)

    # Count all edges
    score = cv2.countNonZero(masked)

    # Threshold (tune with real data)
    if score > 1100:
        result = "NO-GO"
    else:
        result = "GO"

    return result, score, edges, masked


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test.py image.jpg")
        sys.exit()

    path = sys.argv[1]
    img = cv2.imread(path)

    if img is None:
        print("Failed to load image")
        sys.exit()

    crop = find_button_crop(img)

    if crop is None:
        print("Button not found")

    result, score, edges, masked = classify_button(crop)

    print("Result:", result)
    print("Score:", score)

    cv2.imshow("Edges", edges)
    cv2.imshow("Masked Button", masked)
    cv2.waitKey(0)
    cv2.destroyAllWindows()