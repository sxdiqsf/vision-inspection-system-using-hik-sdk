import cv2
import numpy as np
import argparse
import os


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

    pad = 20
    x1 = max(x - r - pad, 0)
    y1 = max(y - r - pad, 0)
    x2 = min(x + r + pad, img.shape[1])
    y2 = min(y + r + pad, img.shape[0])

    crop = img[y1:y2, x1:x2]

    if crop.size == 0:
        return None
    
    # Circle center inside cropped image
    cx = x - x1
    cy = y - y1

    # Create mask
    mask = np.zeros(crop.shape[:2], dtype=np.uint8)
    cv2.circle(mask, (cx, cy), r, 255, -1)

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
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return masked_crop



def detect_go_nogo(crop):
    crop = cv2.resize(crop, (300, 300))

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

    edges = cv2.Canny(gray, 60, 150)

    h, w = edges.shape
    Y, X = np.ogrid[:h, :w]
    cx, cy = w // 2, h // 2
    dist = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)

    mask = ((dist > 95) & (dist < 140)).astype(np.uint8) * 255
    rim = cv2.bitwise_and(edges, edges, mask=mask)

    score = cv2.countNonZero(rim)
    result = "NO-GO" if score > 2825 else "GO"

    return result, score


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, help="Path to single image")
    args = parser.parse_args()

    img = cv2.imread(args.image)

    if img is None:
        print("Failed to read image")
        return

    crop = find_button_crop(img)

    if crop is None:
        print("Button not found")
        return

    result, score = detect_go_nogo(crop)

    print("Image :", os.path.basename(args.image))
    print("Score :", score)
    print("Result:", result)


if __name__ == "__main__":
    main()