"""
Module   : Image Preprocessor
Owner    : Document AI Engineer
Purpose  : Deskew, denoise, contrast-normalize scanned docs.
"""

import cv2
import numpy as np
from typing import Literal


PreprocessLevel = Literal["light", "medium", "heavy"]


def preprocess(
    image_bytes: bytes,
    level: PreprocessLevel = "medium",
    target_dpi: int = 300,
) -> np.ndarray:
    """
    Preprocess image for OCR.

    Pipeline:
    1. Decode bytes -> grayscale
    2. Resize to target DPI (if metadata available)
    3. Deskew (minAreaRect on text contours)
    4. Denoise (fastNlMeansDenoising)
    5. Contrast normalization (CLAHE or adaptive threshold)

    Returns enhanced grayscale image as numpy array.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

    if img is None:
        raise ValueError("Failed to decode image")

    if level == "light":
        return _preprocess_light(img)
    elif level == "heavy":
        return _preprocess_heavy(img)
    else:
        return _preprocess_medium(img)


def _preprocess_light(img: np.ndarray) -> np.ndarray:
    """Light preprocessing: just denoise + slight contrast."""
    denoised = cv2.fastNlMeansDenoising(img, h=10)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(denoised)


def _preprocess_medium(img: np.ndarray) -> np.ndarray:
    """Medium preprocessing: deskew + denoise + CLAHE."""
    deskewed = _deskew(img)
    denoised = cv2.fastNlMeansDenoising(deskewed, h=10)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


def _preprocess_heavy(img: np.ndarray) -> np.ndarray:
    """Heavy preprocessing: deskew + denoise + adaptive threshold + morphology."""
    deskewed = _deskew(img)
    denoised = cv2.fastNlMeansDenoising(deskewed, h=15)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)
    binary = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    return cleaned


def _deskew(img: np.ndarray) -> np.ndarray:
    """Deskew image using minAreaRect on text contours."""
    _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return img

    largest_contour = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest_contour) < 100:
        return img

    rect = cv2.minAreaRect(largest_contour)
    angle = rect[-1]

    if angle < -45:
        angle = 90 + angle

    if abs(angle) < 0.5:
        return img

    h, w = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    return rotated


def preprocess_pipeline(
    image_bytes: bytes,
    steps: list[str] | None = None,
) -> np.ndarray:
    """Custom preprocessing pipeline for advanced use cases."""
    if steps is None:
        steps = ["decode", "deskew", "denoise", "clahe", "threshold"]

    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

    if img is None:
        raise ValueError("Failed to decode image")

    step_functions = {
        "deskew": _deskew,
        "denoise": lambda x: cv2.fastNlMeansDenoising(x, h=10),
        "clahe": lambda x: cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(x),
        "threshold": lambda x: cv2.threshold(x, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
        "adaptive_threshold": lambda x: cv2.adaptiveThreshold(
            x, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        ),
        "morph_close": lambda x: cv2.morphologyEx(
            x, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        ),
    }

    for step in steps:
        if step in step_functions:
            img = step_functions[step](img)

    return img


__all__ = ["preprocess", "preprocess_pipeline", "PreprocessLevel"]