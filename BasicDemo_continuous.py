# -*- coding: utf-8 -*-
import sys
import cv2
import numpy as np
import threading

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QDockWidget
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap, QColor, QPalette, QFont

from CamOperation_class import CameraOperation
from MvCameraControl_class import *
from MvErrorDefine_const import *
from CameraParams_header import *
from PyUICBasicDemo import Ui_MainWindow
import ctypes


# ─────────────────────────────────────────────
# GO / NO-GO Detection Functions (your methods)
# ─────────────────────────────────────────────

def find_button_crop(img):
    """
    Detects a circular button in the image using HoughCircles.
    Returns a masked crop of the button region, or None if not found.
    """
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
    x1 = max(x - r - pad, 0)
    y1 = max(y - r - pad, 0)
    x2 = min(x + r + pad, img.shape[1])
    y2 = min(y + r + pad, img.shape[0])

    crop = img[y1:y2, x1:x2]

    if crop.size == 0:
        return None

    cx = x - x1
    cy = y - y1

    mask = np.zeros(crop.shape[:2], dtype=np.uint8)
    cv2.circle(mask, (cx, cy), r, 255, -1)

    masked_crop = cv2.bitwise_and(crop, crop, mask=mask)

    return masked_crop


def detect_go_nogo(crop):
    """
    Classifies a cropped button image as GO or NO-GO based on edge density.
    Returns: (result_str, score, edges_img, masked_edges_img)
    """
    crop = cv2.resize(crop, (300, 300))

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 60, 150)

    h, w = edges.shape
    Y, X = np.ogrid[:h, :w]
    cx, cy = w // 2, h // 2
    r = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)

    mask = (r < 140).astype(np.uint8) * 255
    masked = cv2.bitwise_and(edges, edges, mask=mask)

    score = cv2.countNonZero(masked)
    result = "NO-GO" if score > 1200 else "GO"

    return result, score, edges, masked


# ─────────────────────────────────────────────
# DEBUG SAVE — remove after testing
# ─────────────────────────────────────────────

import os
from datetime import datetime

def save_debug_result(original_img, crop_img, edges_img, masked_img, result, score,
                      save_dir="gonogo_debug"):
    """
    Saves a single combined debug image containing:
      [Original frame] | [Button crop] | [Raw edges] | [Masked edges]
    with result and score burned in as text.

    All panels are resized to the same height (300 px) before stitching.
    Files are saved as:  YYYYMMDD_HHMMSS_SSS_<RESULT>.jpg

    TEMPORARY — remove this function and its call in GoNoGoProcessor._loop()
    once testing is done.
    """
    os.makedirs(save_dir, exist_ok=True)

    TARGET_H = 300

    def _resize_to_height(img, h):
        """Resize any BGR or grayscale image to a fixed height, keeping aspect ratio."""
        if img is None:
            # Return a black placeholder panel
            return np.zeros((h, h, 3), dtype=np.uint8)
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        ratio = h / img.shape[0]
        new_w = max(1, int(img.shape[1] * ratio))
        return cv2.resize(img, (new_w, h))

    # ── Resize all panels to same height ──
    panel_orig   = _resize_to_height(original_img, TARGET_H)
    panel_crop   = _resize_to_height(crop_img,     TARGET_H)
    panel_edges  = _resize_to_height(edges_img,    TARGET_H)
    panel_masked = _resize_to_height(masked_img,   TARGET_H)

    # ── Label each panel ──
    def _label(img, text):
        out = img.copy()
        cv2.putText(out, text, (6, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(out, text, (6, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0),       1, cv2.LINE_AA)
        return out

    panel_orig   = _label(panel_orig,   "Original")
    panel_crop   = _label(panel_crop,   "Crop")
    panel_edges  = _label(panel_edges,  "Edges")
    panel_masked = _label(panel_masked, f"Masked  score:{score}")

    # ── Stitch horizontally ──
    combined = np.hstack([panel_orig, panel_crop, panel_edges, panel_masked])

    # ── Burn result banner across the top ──
    banner_h = 40
    banner = np.zeros((banner_h, combined.shape[1], 3), dtype=np.uint8)
    color = (0, 200, 80) if result == "GO" else (0, 0, 220)
    banner[:] = color
    label_text = f"  {result}    score: {score}    {datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}"
    cv2.putText(banner, label_text, (10, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)

    final = np.vstack([banner, combined])

    # ── Save ──
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]   # ms precision
    filename = f"{ts}_{result}.jpg"
    filepath = os.path.join(save_dir, filename)
    cv2.imwrite(filepath, final)
    print(f"[DEBUG SAVE] {filepath}")

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
                    crop = find_button_crop(img)
                    if crop is not None and crop.size > 0:
                        result, score, edges, masked = detect_go_nogo(crop)
                        self.callback(result, score, crop, masked)
                        # DEBUG SAVE — remove after testing
                        save_debug_result(img, crop, edges, masked, result, score)
                    else:
                        self.callback("NO BUTTON", 0, None, None)
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
        self.setFixedWidth(320)
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
        self.lbl_score = QLabel("Edge Score: —")
        self.lbl_score.setAlignment(Qt.AlignCenter)
        self.lbl_score.setFont(QFont("Courier New", 11))
        self.lbl_score.setStyleSheet("color: #cccccc;")
        layout.addWidget(self.lbl_score)

        # ── Crop preview row ──
        preview_row = QHBoxLayout()

        self.lbl_crop_title = QLabel("Button Crop")
        self.lbl_crop_title.setAlignment(Qt.AlignCenter)
        self.lbl_crop_title.setFont(QFont("Courier New", 9))
        self.lbl_crop_title.setStyleSheet("color: #888;")

        self.lbl_edges_title = QLabel("Masked Edges")
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

        if result == "GO":
            color = "#00cc66"
            bg = "#0a2e1a"
        elif result == "NO-GO":
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
            masked_bgr = cv2.cvtColor(masked_img, cv2.COLOR_GRAY2BGR)
            self._set_label_image(self.lbl_edges, masked_bgr)
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

    ui_refresh_timer.timeout.connect(_refresh_ui)

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
            get_param()
            isOpen = True
            enable_controls()

    def start_grabbing():
        """
        Starts the camera stream AND launches the GO/NO-GO processor thread.
        The processor reads frames independently; results are pushed to the
        overlay widget every 100 ms via ui_refresh_timer.
        """
        global obj_cam_operation, isGrabbing, gonogo_processor

        ret = obj_cam_operation.Start_grabbing(ui.widgetDisplay.winId())
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
        ret = obj_cam_operation.Save_Bmp()
        if ret != MV_OK:
            QMessageBox.warning(mainWindow, "Error", "Save BMP failed ret:" + ToHexStr(ret), QMessageBox.Ok)
        else:
            print("Save image success")

    def is_float(s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def get_param():
        ret = obj_cam_operation.Get_parameter()
        if ret != MV_OK:
            QMessageBox.warning(mainWindow, "Error", "Get param failed ret:" + ToHexStr(ret), QMessageBox.Ok)
        else:
            ui.edtExposureTime.setText("{0:.2f}".format(obj_cam_operation.exposure_time))
            ui.edtGain.setText("{0:.2f}".format(obj_cam_operation.gain))
            ui.edtFrameRate.setText("{0:.2f}".format(obj_cam_operation.frame_rate))

    def set_param():
        frame_rate = ui.edtFrameRate.text()
        exposure = ui.edtExposureTime.text()
        gain = ui.edtGain.text()
        if not (is_float(frame_rate) and is_float(exposure) and is_float(gain)):
            QMessageBox.warning(mainWindow, "Error", "Set param failed ret:" + ToHexStr(MV_E_PARAMETER), QMessageBox.Ok)
            return MV_E_PARAMETER
        ret = obj_cam_operation.Set_parameter(frame_rate, exposure, gain)
        if ret != MV_OK:
            QMessageBox.warning(mainWindow, "Error", "Set param failed ret:" + ToHexStr(ret), QMessageBox.Ok)
        return MV_OK

    def enable_controls():
        global isGrabbing, isOpen
        ui.groupGrab.setEnabled(isOpen)
        ui.groupParam.setEnabled(isOpen)
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
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(30, 30, 30))
    dark_palette.setColor(QPalette.WindowText, QColor(220, 220, 220))
    dark_palette.setColor(QPalette.Base, QColor(20, 20, 20))
    dark_palette.setColor(QPalette.AlternateBase, QColor(40, 40, 40))
    dark_palette.setColor(QPalette.Button, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.ButtonText, QColor(220, 220, 220))
    app.setPalette(dark_palette)

    mainWindow = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(mainWindow)

    # ── Add GO/NO-GO panel as a dock widget — central widget untouched ──
    overlay_widget = GoNoGoOverlay()
    overlay_widget.setStyleSheet("background: #1e1e1e;")

    dock = QDockWidget("GO / NO-GO Inspector", mainWindow)
    dock.setWidget(overlay_widget)
    dock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
    dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
    mainWindow.addDockWidget(Qt.RightDockWidgetArea, dock)

    # ── Connect signals ──
    ui.bnEnum.clicked.connect(enum_devices)
    ui.bnOpen.clicked.connect(open_device)
    ui.bnClose.clicked.connect(close_device)
    ui.bnStart.clicked.connect(start_grabbing)
    ui.bnStop.clicked.connect(stop_grabbing)
    ui.bnSoftwareTrigger.clicked.connect(trigger_once)
    ui.radioTriggerMode.clicked.connect(set_software_trigger_mode)
    ui.radioContinueMode.clicked.connect(set_continue_mode)
    ui.bnGetParam.clicked.connect(get_param)
    ui.bnSetParam.clicked.connect(set_param)
    ui.bnSaveImage.clicked.connect(save_bmp)

    mainWindow.setWindowTitle("HIK Camera — GO / NO-GO Inspector")
    mainWindow.show()

    app.exec_()

    close_device()
    MvCamera.MV_CC_Finalize()
    sys.exit()