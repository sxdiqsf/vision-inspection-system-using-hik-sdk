# -*- coding: utf-8 -*-
import sys
import cv2
import numpy as np
import threading
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QWidget,QSizePolicy,
    QVBoxLayout, QHBoxLayout, QLabel, QDockWidget
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap, QColor, QPalette, QFont

from CamOperation_class import CameraOperation
from MvCameraControl_class import *
from MvErrorDefine_const import *
from CameraParams_header import *
from PyUICBasicDemo import Ui_MainWindow,apply_styles
import ctypes
import glob
from datetime import datetime

# Toggle: whether debug saves are enabled
global is_debug_save_enabled
is_debug_save_enabled = False
global detected_holes_memory
detected_holes_memory = []
# ─────────────────────────────────────────────
# HOLE DETECTION LOGIC
# ─────────────────────────────────────────────

# def detect_holes(image):

#     output = image.copy()

#     H, W = image.shape[:2]

#     # =====================================================
#     # FIXED ROI WINDOW
#     # =====================================================

#     ROI_W = 900
#     ROI_H = 700

#     x1 = (W - ROI_W) // 2
#     y1 = (H - ROI_H) // 2

#     x2 = x1 + ROI_W
#     y2 = y1 + ROI_H

#     # Draw ROI
#     cv2.rectangle(
#         output,
#         (x1, y1),
#         (x2, y2),
#         (0, 255, 255),
#         3
#     )

#     # =====================================================
#     # PROCESS ONLY ROI
#     # =====================================================

#     roi = image[y1:y2, x1:x2]

#     gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

#     # CLAHE improves local contrast
#     clahe = cv2.createCLAHE(
#         clipLimit=2.0,
#         tileGridSize=(8, 8)
#     )

#     gray = clahe.apply(gray)

#     # Blur
#     blur = cv2.GaussianBlur(gray, (5, 5), 0)

#     # =====================================================
#     # THRESHOLD
#     # =====================================================

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

#     # =====================================================
#     # FIND CONTOURS
#     # =====================================================

#     contours, _ = cv2.findContours(
#         thresh,
#         cv2.RETR_EXTERNAL,
#         cv2.CHAIN_APPROX_SIMPLE
#     )

#     hole_count = 0

#     cropped_holes = []

#     # =====================================================
#     # FILTER CIRCULAR OBJECTS
#     # =====================================================

#     for cnt in contours:

#         area = cv2.contourArea(cnt)

#         if area < 100:
#             continue

#         perimeter = cv2.arcLength(cnt, True)

#         if perimeter == 0:
#             continue

#         circularity = 4 * np.pi * area / (perimeter * perimeter)

#         # Circularity filter
#         if circularity < 0.65:
#             continue

#         x, y, w, h = cv2.boundingRect(cnt)

#         aspect_ratio = w / float(h)

#         # Square-like check
#         if aspect_ratio < 0.7 or aspect_ratio > 1.3:
#             continue

#         hole_count += 1        

#         cx = x + w // 2
#         cy = y + h // 2

#         radius = max(w, h) // 2

#         # Convert ROI coords -> image coords
#         gx = cx + x1
#         gy = cy + y1

#         # Draw circle
#         cv2.circle(
#             output,
#             (gx, gy),
#             radius,
#             (0, 255, 0),
#             2
#         )

#         # Center point
#         cv2.circle(
#             output,
#             (gx, gy),
#             3,
#             (0, 0, 255),
#             -1
#         )

#         # Label
#         cv2.putText(
#             output,
#             f"H{hole_count}",
#             (gx - 20, gy - radius - 10),
#             cv2.FONT_HERSHEY_SIMPLEX,
#             0.7,
#             (255, 0, 0),
#             2
#         )

#         # =====================================================
#         # CROP AROUND HOLE
#         # =====================================================

#         crop_size = 120

#         cx1 = max(gx - crop_size, 0)
#         cy1 = max(gy - crop_size, 0)

#         cx2 = min(gx + crop_size, W)
#         cy2 = min(gy + crop_size, H)

#         crop = image[cy1:cy2, cx1:cx2]

#         cropped_holes.append(crop)
#         global is_debug_save_enabled

#         if is_debug_save_enabled:

#             save_dir = "saved_holes"

#             os.makedirs(save_dir, exist_ok=True)

#             timestamp = datetime.now().strftime(
#                 "%Y%m%d_%H%M%S_%f"
#             )

#             filename = os.path.join(
#                 save_dir,
#                 f"hole_{hole_count}_{timestamp}.png"
#             )

#             cv2.imwrite(filename, crop)

#             print(f"[SAVED] {filename}")

#     # =====================================================
#     # TOTAL COUNT
#     # =====================================================

#     cv2.putText(
#         output,
#         f"TOTAL = {hole_count}",
#         (40, 60),
#         cv2.FONT_HERSHEY_SIMPLEX,
#         1.5,
#         (0, 255, 255),
#         4
#     )

#     # =====================================================
#     # RESIZE FOR UI
#     # =====================================================

#     output = cv2.resize(
#         output,
#         None,
#         fx=0.5,
#         fy=0.5,
#         interpolation=cv2.INTER_AREA
#     )

#     thresh_vis = cv2.resize(
#         thresh,
#         None,
#         fx=0.5,
#         fy=0.5,
#         interpolation=cv2.INTER_AREA
#     )

#     return hole_count, output, thresh_vis

# def detect_holes(image):

#     output = image.copy()

#     H, W = image.shape[:2]

#     # =====================================================
#     # FIXED ROI WINDOW
#     # =====================================================

#     ROI_W = 900
#     ROI_H = 700

#     x1 = (W - ROI_W) // 2
#     y1 = (H - ROI_H) // 2

#     x2 = x1 + ROI_W
#     y2 = y1 + ROI_H

#     cv2.rectangle(
#         output,
#         (x1, y1),
#         (x2, y2),
#         (0, 255, 255),
#         2
#     )

#     # =====================================================
#     # ROI
#     # =====================================================

#     roi = image[y1:y2, x1:x2]

#     gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

#     # Contrast enhancement
#     clahe = cv2.createCLAHE(
#         clipLimit=2.0,
#         tileGridSize=(8, 8)
#     )

#     gray = clahe.apply(gray)

#     # Blur
#     blur = cv2.GaussianBlur(gray, (7, 7), 1.5)

#     # =====================================================
#     # HOUGH CIRCLE DETECTION
#     # =====================================================

#     circles = cv2.HoughCircles(
#         blur,
#         cv2.HOUGH_GRADIENT,

#         dp=1.2,
#         minDist=60,

#         param1=120,
#         param2=22,

#         # IMPORTANT:
#         # Tune ONLY these 2 values
#         minRadius=28,
#         maxRadius=42
#     )

#     hole_count = 0
#     cropped_holes = []

#     # =====================================================
#     # DRAW DETECTED HOLES
#     # =====================================================

#     if circles is not None:

#         circles = np.round(circles[0, :]).astype("int")

#         for i, (cx, cy, radius) in enumerate(circles):

#             # Convert ROI coords -> image coords
#             gx = cx + x1
#             gy = cy + y1

#             hole_count += 1

#             # Outer circle
#             cv2.circle(
#                 output,
#                 (gx, gy),
#                 radius,
#                 (0, 255, 0),
#                 2
#             )

#             # Center point
#             cv2.circle(
#                 output,
#                 (gx, gy),
#                 3,
#                 (0, 0, 255),
#                 -1
#             )

#             # Label
#             cv2.putText(
#                 output,
#                 f"H{hole_count}",
#                 (gx - 20, gy - radius - 10),
#                 cv2.FONT_HERSHEY_SIMPLEX,
#                 0.7,
#                 (255, 0, 0),
#                 2
#             )

#             # =====================================================
#             # CROP
#             # =====================================================

#             crop_size = 120

#             cx1 = max(gx - crop_size, 0)
#             cy1 = max(gy - crop_size, 0)

#             cx2 = min(gx + crop_size, W)
#             cy2 = min(gy + crop_size, H)

#             crop = image[cy1:cy2, cx1:cx2]

#             cropped_holes.append(crop)

#     # =====================================================
#     # TOTAL COUNT
#     # =====================================================

#     cv2.putText(
#         output,
#         f"TOTAL = {hole_count}",
#         (40, 60),
#         cv2.FONT_HERSHEY_SIMPLEX,
#         1.5,
#         (0, 255, 255),
#         4
#     )

#     thresh_vis = cv2.resize(
#         blur,
#         None,
#         fx=0.5,
#         fy=0.5,
#         interpolation=cv2.INTER_AREA
#     )

#     output = cv2.resize(
#         output,
#         None,
#         fx=0.5,
#         fy=0.5,
#         interpolation=cv2.INTER_AREA
#     )

#     return hole_count, output, thresh_vis

def detect_holes(image):

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Binary threshold
    _, thresh = cv2.threshold(
        blur,
        80,
        255,
        cv2.THRESH_BINARY_INV
    )

    # Remove small noise
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

        # Ignore tiny noise
        if area < 100:
            continue

        perimeter = cv2.arcLength(cnt, True)

        if perimeter == 0:
            continue

        # Circularity
        circularity = (
            4 * np.pi * area /
            (perimeter * perimeter)
        )

        if circularity < 0.7:
            continue

        x, y, w, h = cv2.boundingRect(cnt)

        aspect_ratio = w / float(h)

        # Near circular shape
        if aspect_ratio < 0.75 or aspect_ratio > 1.25:
            continue

        cx = x + w // 2
        cy = y + h // 2

        holes.append((cx, cy, w, h))

    holes = sorted(holes, key=lambda h: h[0])

    return holes, thresh


# ---------------------------------------------------
# MAIN METHOD
# ---------------------------------------------------

def detect_holes(image):

    output = image.copy()

    H, W = image.shape[:2]

    # =====================================================
    # FIXED CENTER WINDOW
    # =====================================================

    ROI_W = 900
    ROI_H = 700

    x1 = (W - ROI_W) // 2
    y1 = (H - ROI_H) // 2

    x2 = x1 + ROI_W
    y2 = y1 + ROI_H

    # Draw ROI window
    cv2.rectangle(
        output,
        (x1, y1),
        (x2, y2),
        (0, 255, 255),
        2
    )

    # =====================================================
    # PROCESS ONLY ROI
    # =====================================================

    roi = image[y1:y2, x1:x2]

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

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

    hole_count = len(detected_holes_memory)

    for cnt in contours:

        area = cv2.contourArea(cnt)

        if area < 100:
            continue

        perimeter = cv2.arcLength(cnt, True)

        if perimeter == 0:
            continue

        circularity = (
            4 * np.pi * area /
            (perimeter * perimeter)
        )

        if circularity < 0.7:
            continue

        x, y, w, h = cv2.boundingRect(cnt)

        aspect_ratio = w / float(h)

        if aspect_ratio < 0.75 or aspect_ratio > 1.25:
            continue

        # ROI coords
        cx = x + w // 2
        cy = y + h // 2

        # Full image coords
        gx = cx + x1
        gy = cy + y1

        radius = max(w, h) // 2

        # =====================================================
        # CHECK MEMORY
        # =====================================================

        is_new_hole = True

        for px, py in detected_holes_memory:

            distance = np.sqrt(
                (gx - px) ** 2 +
                (gy - py) ** 2
            )

            if distance < 40:

                is_new_hole = False
                break

        # =====================================================
        # NEW HOLE
        # =====================================================

        if is_new_hole:

            detected_holes_memory.append((gx, gy))

            hole_count += 1

            color = (0, 255, 0)

        else:

            color = (255, 0, 0)

        # =====================================================
        # DRAW
        # =====================================================

        cv2.circle(
            output,
            (gx, gy),
            radius,
            color,
            2
        )

        cv2.circle(
            output,
            (gx, gy),
            3,
            (0, 0, 255),
            -1
        )

        cv2.putText(
            output,
            str(hole_count),
            (gx - 10, gy - radius - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2
        )
        

        is_new_hole = True

        for px, py in detected_holes_memory:

            distance = np.sqrt(
                (gx - px) ** 2 +
                (gy - py) ** 2
            )

            # Same hole already counted
            if distance < 40:

                is_new_hole = False
                break

        # ------------------------------------------------
        # COUNT ONLY NEW HOLES
        # ------------------------------------------------

        if is_new_hole:

            detected_holes_memory.append((gx, gy))

            hole_count += 1

            # Draw GREEN = new counted hole
            cv2.circle(
                output,
                (gx, gy),
                radius,
                (0, 255, 0),
                2
            )

            cv2.putText(
                output,
                str(hole_count),
                (gx - 10, gy - radius - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

        else:

            # Already counted hole
            # Draw BLUE
            cv2.circle(
                output,
                (gx, gy),
                radius,
                (255, 0, 0),
                2
            )

    # =====================================================
    # TOTAL COUNT
    # =====================================================

    cv2.putText(
        output,
        f"TOTAL: {hole_count}",
        (40, 90),
        cv2.FONT_HERSHEY_SIMPLEX,
        2.2,
        (0, 255, 255),
        5
    )

    # =====================================================
    # THRESH VIS
    # =====================================================

    thresh_vis = cv2.cvtColor(
        thresh,
        cv2.COLOR_GRAY2BGR
    )

    return hole_count, output, thresh_vis


# ─────────────────────────────────────────────
# Frame Processor: runs in a background thread
# ─────────────────────────────────────────────

class GoNoGoProcessor:
    """
    Continuously grabs the latest frame from the camera using GetImageBuffer,
    runs GO/NO-GO detection, and emits results via a callback.
    """

    def __init__(self, cam_operation_ref, result_callback):
        self.cam_op = cam_operation_ref
        self.callback = result_callback
        self._running = False
        self._thread = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        stOutFrame = MV_FRAME_OUT()
        ctypes.memset(ctypes.byref(stOutFrame), 0, ctypes.sizeof(stOutFrame))

        while self._running:
            ret = self.cam_op.obj_cam.MV_CC_GetImageBuffer(stOutFrame, 1000)
            if ret != MV_OK:
                continue

            try:
                img = self._frame_to_bgr(stOutFrame)

                if img is not None:
                    hole_count, result_img, thresh_img = detect_holes(img)

                    self.callback(
                            f"COUNT: {hole_count}",
                            hole_count,
                            result_img,
                            thresh_img
                        )
            finally:
                self.cam_op.obj_cam.MV_CC_FreeImageBuffer(stOutFrame)

    def _frame_to_bgr(self, frame):
        """Convert MV_FRAME_OUT to a BGR numpy array."""
        try:
            pixel_fmt = frame.stFrameInfo.enPixelType
            w = frame.stFrameInfo.nWidth
            h = frame.stFrameInfo.nHeight
            buf_size = frame.stFrameInfo.nFrameLen

            raw = (ctypes.c_ubyte * buf_size)()
            ctypes.memmove(raw, frame.pBufAddr, buf_size)
            arr = np.frombuffer(raw, dtype=np.uint8)

            # Common pixel format handling
            if pixel_fmt == PixelType_Gvsp_Mono8:
                img = arr.reshape((h, w))
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            elif pixel_fmt in (PixelType_Gvsp_RGB8_Packed,):
                img = arr.reshape((h, w, 3))
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            elif pixel_fmt in (PixelType_Gvsp_BayerRG8, PixelType_Gvsp_BayerGR8,
                               PixelType_Gvsp_BayerBG8, PixelType_Gvsp_BayerGB8):
                img = arr.reshape((h, w))
                bayer_map = {
                    PixelType_Gvsp_BayerRG8: cv2.COLOR_BayerRG2BGR,
                    PixelType_Gvsp_BayerGR8: cv2.COLOR_BayerGR2BGR,
                    PixelType_Gvsp_BayerBG8: cv2.COLOR_BayerBG2BGR,
                    PixelType_Gvsp_BayerGB8: cv2.COLOR_BayerGB2BGR,
                }
                img = cv2.cvtColor(img, bayer_map[pixel_fmt])
            else:
                # Fallback: try treating as mono
                img = arr.reshape((h, w)) if arr.size == h * w else None

            return img
        except Exception as e:
            print(f"[GoNoGoProcessor] Frame conversion error: {e}")
            return None


# ─────────────────────────────────────────────
# Helper utilities (unchanged from original)
# ─────────────────────────────────────────────

def TxtWrapBy(start_str, end, all):
    start = all.find(start_str)
    if start >= 0:
        start += len(start_str)
        end = all.find(end, start)
        if end >= 0:
            return all[start:end].strip()


def ToHexStr(num):
    chaDic = {10: 'a', 11: 'b', 12: 'c', 13: 'd', 14: 'e', 15: 'f'}
    hexStr = ""
    if num < 0:
        num = num + 2 ** 32
    while num >= 16:
        digit = num % 16
        hexStr = chaDic.get(digit, str(digit)) + hexStr
        num //= 16
    hexStr = chaDic.get(num, str(num)) + hexStr
    return hexStr


def decoding_char(ctypes_char_array):
    byte_str = memoryview(ctypes_char_array).tobytes()
    null_index = byte_str.find(b'\x00')
    if null_index != -1:
        byte_str = byte_str[:null_index]
    for encoding in ['gbk', 'utf-8', 'latin-1']:
        try:
            return byte_str.decode(encoding)
        except UnicodeDecodeError:
            continue
    return byte_str.decode('latin-1', errors='replace')


# ─────────────────────────────────────────────
# Result Overlay Widget
# ─────────────────────────────────────────────

class GoNoGoOverlay(QWidget):
    """
    A floating overlay panel that shows the live GO/NO-GO result,
    edge score, and a small preview of the detected crop + masked edges.
    Attach it next to the camera display widget.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setFixedWidth(320)
        self.setSizePolicy(
        QSizePolicy.Expanding, QSizePolicy.Expanding
            )
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # ── Result badge ──
        self.lbl_result = QLabel("WAITING")
        self.lbl_result.setAlignment(Qt.AlignCenter)
        self.lbl_result.setFixedHeight(64)
        font = QFont("Courier New", 22, QFont.Bold)
        self.lbl_result.setFont(font)
        self.lbl_result.setStyleSheet("""
            QLabel {
                background: #2a2a2a;
                color: #aaaaaa;
                border-radius: 8px;
                letter-spacing: 3px;
            }
        """)
        layout.addWidget(self.lbl_result)

        # ── Score ──
        self.lbl_score = QLabel("Count: —")
        self.lbl_score.setAlignment(Qt.AlignCenter)
        self.lbl_score.setFont(QFont("Courier New", 11))
        self.lbl_score.setStyleSheet("color: #cccccc;")
        layout.addWidget(self.lbl_score)

        # ── Crop preview row ──
        preview_row = QHBoxLayout()

        self.lbl_crop_title = QLabel("Hole detection")
        self.lbl_crop_title.setAlignment(Qt.AlignCenter)
        self.lbl_crop_title.setFont(QFont("Courier New", 9))
        self.lbl_crop_title.setStyleSheet("color: #888;")

        self.lbl_edges_title = QLabel("Threshold / Debug")
        self.lbl_edges_title.setAlignment(Qt.AlignCenter)
        self.lbl_edges_title.setFont(QFont("Courier New", 9))
        self.lbl_edges_title.setStyleSheet("color: #888;")

        col1 = QVBoxLayout()
        col1.addWidget(self.lbl_crop_title)
        self.lbl_crop = QLabel()
        self.lbl_crop.setFixedSize(140, 140)
        self.lbl_crop.setAlignment(Qt.AlignCenter)
        self.lbl_crop.setStyleSheet("background: #1a1a1a; border-radius: 4px;")
        col1.addWidget(self.lbl_crop)

        col2 = QVBoxLayout()
        col2.addWidget(self.lbl_edges_title)
        self.lbl_edges = QLabel()
        self.lbl_edges.setFixedSize(140, 140)
        self.lbl_edges.setAlignment(Qt.AlignCenter)
        self.lbl_edges.setStyleSheet("background: #1a1a1a; border-radius: 4px;")
        col2.addWidget(self.lbl_edges)

        preview_row.addLayout(col1)
        preview_row.addLayout(col2)
        layout.addLayout(preview_row)

        # ── Threshold note ──
        self.lbl_threshold = QLabel("Threshold: score > 1200 → NO-GO")
        self.lbl_threshold.setAlignment(Qt.AlignCenter)
        self.lbl_threshold.setFont(QFont("Courier New", 9))
        self.lbl_threshold.setStyleSheet("color: #555;")
        layout.addWidget(self.lbl_threshold)

        layout.addStretch()

    def update_result(self, result, score, crop_img, masked_img):
        """Call this from the main thread via QTimer/signal to update UI."""

        if "COUNT" in result:

            color = "#00cc66"
            bg = "#0a2e1a"

        elif result == "DETECTING...":

            color = "#ffaa00"
            bg = "#3a2a00"

        elif result == "NO HOLES":

            color = "#ff3333"
            bg = "#2e0a0a"

        else:

            color = "#aaaaaa"
            bg = "#2a2a2a"

        self.lbl_result.setText(result)
        self.lbl_result.setStyleSheet(f"""
            QLabel {{
                background: {bg};
                color: {color};
                border-radius: 8px;
                letter-spacing: 3px;
                border: 2px solid {color};
            }}
        """)

        self.lbl_score.setText(f"Edge Score: {score}")

        if crop_img is not None:
            self._set_label_image(self.lbl_crop, crop_img)
        else:
            self.lbl_crop.clear()
            self.lbl_crop.setText("No button\ndetected")
            self.lbl_crop.setStyleSheet("background: #1a1a1a; color: #555; border-radius: 4px;")

        if masked_img is not None:
            self._set_label_image(self.lbl_edges, masked_img)
        else:
            self.lbl_edges.clear()

    def _set_label_image(self, label, bgr_img):
        """Convert a BGR numpy array to QPixmap and display in a QLabel."""
        rgb = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg).scaled(
            label.width(), label.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        label.setPixmap(pix)


# ─────────────────────────────────────────────
# Main Application
# ─────────────────────────────────────────────

if __name__ == "__main__":

    MvCamera.MV_CC_Initialize()

    global deviceList
    deviceList = MV_CC_DEVICE_INFO_LIST()
    global cam
    cam = MvCamera()
    global nSelCamIndex
    nSelCamIndex = 0
    global obj_cam_operation
    obj_cam_operation = 0
    global isOpen
    isOpen = False
    global isGrabbing
    isGrabbing = False
    global isCalibMode
    isCalibMode = True

    # GO/NOGO processor instance (created on start_grabbing)
    global gonogo_processor
    gonogo_processor = None

    # ── Latest result cache (written by bg thread, read by QTimer on main thread) ──
    _latest_result = {"result": None, "score": 0, "crop": None, "masked": None}
    _result_lock = threading.Lock()

    def _on_gonogo_result(result, score, crop, masked):
        """Called from background thread — just cache, don't touch Qt here."""
        with _result_lock:
            _latest_result["result"] = result
            _latest_result["score"] = score
            _latest_result["crop"] = crop.copy() if crop is not None else None
            _latest_result["masked"] = masked.copy() if masked is not None else None

    # QTimer polls the cache and pushes to UI safely on the main thread
    ui_refresh_timer = QTimer()

    def _refresh_ui():
        with _result_lock:
            r = _latest_result["result"]
            s = _latest_result["score"]
            c = _latest_result["crop"]
            m = _latest_result["masked"]
        if r is not None:
            overlay_widget.update_result(r, s, c, m)
        
        if c is not None:
            show_main_image(c)

    ui_refresh_timer.timeout.connect(_refresh_ui)

    def show_main_image(img):

        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        h, w, ch = rgb.shape

        qimg = QImage(
            rgb.data,
            w,
            h,
            ch * w,
            QImage.Format_RGB888
        )

        pix = QPixmap.fromImage(qimg)

        pix = pix.scaled(
            ui.widgetDisplay.width(),
            ui.widgetDisplay.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        ui.widgetDisplay.setPixmap(pix)

    # ── Camera UI callbacks (all unchanged, except start/stop_grabbing) ──

    def enum_devices():
        global deviceList, obj_cam_operation

        deviceList = MV_CC_DEVICE_INFO_LIST()
        n_layer_type = (MV_GIGE_DEVICE | MV_USB_DEVICE | MV_GENTL_CAMERALINK_DEVICE
                        | MV_GENTL_CXP_DEVICE | MV_GENTL_XOF_DEVICE)
        ret = MvCamera.MV_CC_EnumDevices(n_layer_type, deviceList)
        if ret != 0:
            QMessageBox.warning(mainWindow, "Error", "Enum devices fail! ret = :" + ToHexStr(ret), QMessageBox.Ok)
            return ret

        if deviceList.nDeviceNum == 0:
            QMessageBox.warning(mainWindow, "Info", "Find no device", QMessageBox.Ok)
            return ret

        print("Find %d devices!" % deviceList.nDeviceNum)
        devList = []

        for i in range(0, deviceList.nDeviceNum):
            mvcc_dev_info = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
            if mvcc_dev_info.nTLayerType in (MV_GIGE_DEVICE, MV_GENTL_GIGE_DEVICE):
                info = mvcc_dev_info.SpecialInfo.stGigEInfo
                name = decoding_char(info.chUserDefinedName)
                model = decoding_char(info.chModelName)
                ip = info.nCurrentIp
                nip = ((ip >> 24) & 0xff, (ip >> 16) & 0xff, (ip >> 8) & 0xff, ip & 0xff)
                devList.append(f"[{i}]GigE: {name} {model}({'.'.join(map(str,nip))})")
            elif mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
                info = mvcc_dev_info.SpecialInfo.stUsb3VInfo
                name = decoding_char(info.chUserDefinedName)
                model = decoding_char(info.chModelName)
                sn = "".join(chr(c) for c in info.chSerialNumber if c != 0)
                devList.append(f"[{i}]USB: {name} {model}({sn})")
            elif mvcc_dev_info.nTLayerType == MV_GENTL_CAMERALINK_DEVICE:
                info = mvcc_dev_info.SpecialInfo.stCMLInfo
                name = decoding_char(info.chUserDefinedName)
                model = decoding_char(info.chModelName)
                sn = "".join(chr(c) for c in info.chSerialNumber if c != 0)
                devList.append(f"[{i}]CML: {name} {model}({sn})")
            elif mvcc_dev_info.nTLayerType == MV_GENTL_CXP_DEVICE:
                info = mvcc_dev_info.SpecialInfo.stCXPInfo
                name = decoding_char(info.chUserDefinedName)
                model = decoding_char(info.chModelName)
                sn = "".join(chr(c) for c in info.chSerialNumber if c != 0)
                devList.append(f"[{i}]CXP: {name} {model}({sn})")
            elif mvcc_dev_info.nTLayerType == MV_GENTL_XOF_DEVICE:
                info = mvcc_dev_info.SpecialInfo.stXoFInfo
                name = decoding_char(info.chUserDefinedName)
                model = decoding_char(info.chModelName)
                sn = "".join(chr(c) for c in info.chSerialNumber if c != 0)
                devList.append(f"[{i}]XoF: {name} {model}({sn})")

        ui.ComboDevices.clear()
        ui.ComboDevices.addItems(devList)
        ui.ComboDevices.setCurrentIndex(0)

    def open_device():
        global deviceList, nSelCamIndex, obj_cam_operation, isOpen
        if isOpen:
            QMessageBox.warning(mainWindow, "Error", 'Camera is Running!', QMessageBox.Ok)
            return MV_E_CALLORDER

        nSelCamIndex = ui.ComboDevices.currentIndex()
        if nSelCamIndex < 0:
            QMessageBox.warning(mainWindow, "Error", 'Please select a camera!', QMessageBox.Ok)
            return MV_E_CALLORDER

        obj_cam_operation = CameraOperation(cam, deviceList, nSelCamIndex)
        ret = obj_cam_operation.Open_device()
        if ret != 0:
            QMessageBox.warning(mainWindow, "Error", "Open device failed ret:" + ToHexStr(ret), QMessageBox.Ok)
            isOpen = False
        else:
            set_continue_mode()
            isOpen = True
            enable_controls()

    def start_grabbing():
        """
        Starts the camera stream AND launches the GO/NO-GO processor thread.
        The processor reads frames independently; results are pushed to the
        overlay widget every 100 ms via ui_refresh_timer.
        """
        global obj_cam_operation, isGrabbing, gonogo_processor

        # ret = obj_cam_operation.Start_grabbing(ui.widgetDisplay.winId())
        ret = obj_cam_operation.Start_grabbing(0)
        if ret != 0:
            QMessageBox.warning(mainWindow, "Error", "Start grabbing failed ret:" + ToHexStr(ret), QMessageBox.Ok)
            return

        isGrabbing = True
        enable_controls()

        # Start GO/NO-GO background processor
        gonogo_processor = GoNoGoProcessor(obj_cam_operation, _on_gonogo_result)
        gonogo_processor.start()

        # Refresh UI every 100 ms (10 fps display update for overlay)
        ui_refresh_timer.start(100)

        overlay_widget.update_result("DETECTING...", 0, None, None)
        print("[GO/NOGO] Processor started.")

    def stop_grabbing():
        global obj_cam_operation, isGrabbing, gonogo_processor
        global is_debug_save_enabled
        is_debug_save_enabled = False
        ui.bnSaveImage.setText("Save Image")
        ui.bnSaveImage.setStyleSheet("")
        # Stop GO/NO-GO processor first
        if gonogo_processor is not None:
            gonogo_processor.stop()
        ui_refresh_timer.stop()
        overlay_widget.update_result("WAITING", 0, None, None)

        ret = obj_cam_operation.Stop_grabbing()
        if ret != 0:
            QMessageBox.warning(mainWindow, "Error", "Stop grabbing failed ret:" + ToHexStr(ret), QMessageBox.Ok)
        else:
            isGrabbing = False
            enable_controls()
        print("[GO/NOGO] Processor stopped.")

    def close_device():
        global isOpen, isGrabbing, obj_cam_operation, gonogo_processor
        global is_debug_save_enabled
        is_debug_save_enabled = False
        ui.bnSaveImage.setText("Save Image")
        ui.bnSaveImage.setStyleSheet("")

        if gonogo_processor is not None:
            gonogo_processor.stop()
        ui_refresh_timer.stop()

        if isOpen:
            obj_cam_operation.Close_device()
            isOpen = False

        isGrabbing = False
        enable_controls()

    def set_continue_mode():
        ret = obj_cam_operation.Set_trigger_mode(False)
        if ret != 0:
            QMessageBox.warning(mainWindow, "Error", "Set continue mode failed ret:" + ToHexStr(ret), QMessageBox.Ok)
        else:
            ui.radioContinueMode.setChecked(True)
            ui.radioTriggerMode.setChecked(False)
            ui.bnSoftwareTrigger.setEnabled(False)

    def set_software_trigger_mode():
        ret = obj_cam_operation.Set_trigger_mode(True)
        if ret != 0:
            QMessageBox.warning(mainWindow, "Error", "Set trigger mode failed ret:" + ToHexStr(ret), QMessageBox.Ok)
        else:
            ui.radioContinueMode.setChecked(False)
            ui.radioTriggerMode.setChecked(True)
            ui.bnSoftwareTrigger.setEnabled(isGrabbing)

    def trigger_once():
        ret = obj_cam_operation.Trigger_once()
        if ret != 0:
            QMessageBox.warning(mainWindow, "Error", "TriggerSoftware failed ret:" + ToHexStr(ret), QMessageBox.Ok)

    def save_bmp():
        global is_debug_save_enabled
        is_debug_save_enabled = not is_debug_save_enabled

        if is_debug_save_enabled:
            ui.bnSaveImage.setText("⏺ Saving ON")
            ui.bnSaveImage.setStyleSheet("""
                QPushButton {
                    background-color: #8b0000;
                    color: white;
                    font-weight: bold;
                    border-radius: 4px;
                    padding: 4px;
                }
            """)
            print("[DEBUG SAVE] Auto-save ENABLED")
        else:
            ui.bnSaveImage.setText("Save Image")
            ui.bnSaveImage.setStyleSheet("")      # revert to app default
            print("[DEBUG SAVE] Auto-save DISABLED")

    def is_float(s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def enable_controls():
        global isGrabbing, isOpen
        ui.groupGrab.setEnabled(isOpen)
        # ui.groupParam.setEnabled(isOpen)  ← deleted
        ui.bnOpen.setEnabled(not isOpen)
        ui.bnClose.setEnabled(isOpen)
        ui.bnStart.setEnabled(isOpen and not isGrabbing)
        ui.bnStop.setEnabled(isOpen and isGrabbing)
        ui.bnSoftwareTrigger.setEnabled(isGrabbing and ui.radioTriggerMode.isChecked())
        ui.bnSaveImage.setEnabled(isOpen and isGrabbing)

    # ── Build the window ──
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Dark palette
    # dark_palette = QPalette()
    # dark_palette.setColor(QPalette.Window, QColor(30, 30, 30))
    # dark_palette.setColor(QPalette.WindowText, QColor(220, 220, 220))
    # dark_palette.setColor(QPalette.Base, QColor(20, 20, 20))
    # dark_palette.setColor(QPalette.AlternateBase, QColor(40, 40, 40))
    # dark_palette.setColor(QPalette.Button, QColor(45, 45, 45))
    # dark_palette.setColor(QPalette.ButtonText, QColor(220, 220, 220))
    # app.setPalette(dark_palette)
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window,          QColor(30,  30,  30))
    dark_palette.setColor(QPalette.WindowText,      QColor(220, 220, 220))
    dark_palette.setColor(QPalette.Base,            QColor(20,  20,  20))
    dark_palette.setColor(QPalette.AlternateBase,   QColor(40,  40,  40))
    dark_palette.setColor(QPalette.ToolTipBase,     QColor(255, 255, 220))
    dark_palette.setColor(QPalette.ToolTipText,     QColor(0,   0,   0))
    dark_palette.setColor(QPalette.Text,            QColor(220, 220, 220))
    dark_palette.setColor(QPalette.Button,          QColor(45,  45,  45))
    dark_palette.setColor(QPalette.ButtonText,      QColor(220, 220, 220))
    dark_palette.setColor(QPalette.BrightText,      QColor(255, 0,   0))
    dark_palette.setColor(QPalette.Highlight,       QColor(41,  121, 255))
    dark_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(dark_palette)
    # app.setStyleSheet("""
    #     QMainWindow, QWidget {
    #         background-color: #1e1e1e;
    #         color: #e0e0e0;
    #     }
    #     QStatusBar { background: #181818; color: #888; }
    # """)
    mainWindow = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(mainWindow)

    # =====================================================
# Replace widgetDisplay with QLabel
# =====================================================

    from PyQt5.QtWidgets import QLabel

    camera_label = QLabel()

    camera_label.setAlignment(Qt.AlignCenter)

    camera_label.setStyleSheet("""
        background-color: black;
        border: 2px solid #444;
    """)

    # Copy size policy
    camera_label.setSizePolicy(ui.widgetDisplay.sizePolicy())

    # Replace widget inside layout
    parent_layout = ui.widgetDisplay.parentWidget().layout()

    parent_layout.replaceWidget(ui.widgetDisplay, camera_label)

    # Remove old widget
    ui.widgetDisplay.deleteLater()

    # Assign new label
    ui.widgetDisplay = camera_label
    # ── Add GO/NO-GO panel as a dock widget — central widget untouched ──
    # overlay_widget = GoNoGoOverlay()
    # overlay_widget.setStyleSheet("background: #1e1e1e;")

    # dock = QDockWidget("GO / NO-GO Inspector", mainWindow)
    # dock.setWidget(overlay_widget)
    # dock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
    # dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
    # mainWindow.addDockWidget(Qt.RightDockWidgetArea, dock)

    # ── Embed GO/NO-GO overlay into the right panel slot ──
    overlay_widget = GoNoGoOverlay()
    overlay_widget.setStyleSheet("background: #1e1e1e;")
    ui.gonogoSlotLayout.addWidget(overlay_widget)

    # ── Connect signals ──
    ui.bnEnum.clicked.connect(enum_devices)
    ui.bnOpen.clicked.connect(open_device)
    ui.bnClose.clicked.connect(close_device)
    ui.bnStart.clicked.connect(start_grabbing)
    ui.bnStop.clicked.connect(stop_grabbing)
    ui.bnSoftwareTrigger.clicked.connect(trigger_once)
    ui.radioTriggerMode.clicked.connect(set_software_trigger_mode)
    ui.radioContinueMode.clicked.connect(set_continue_mode)
    ui.bnSaveImage.clicked.connect(save_bmp)

    mainWindow.setWindowTitle("HIK Camera — Hole Counter")
    mainWindow.show()
    apply_styles(ui)

    app.exec_()

    close_device()
    MvCamera.MV_CC_Finalize()
    sys.exit()