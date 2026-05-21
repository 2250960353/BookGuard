import os
from typing import List, Optional
from PIL import Image, ImageEnhance, ImageFilter
import io


def preprocess_image(
    image_path: str,
    grayscale: bool = False,
    denoise: bool = False,
    sharpen: bool = False,
    contrast: float = 1.0,
    brightness: float = 1.0,
    rotate_angle: float = 0,
    auto_rotate: bool = False,
    output_path: Optional[str] = None,
) -> str:
    img = Image.open(image_path)

    if rotate_angle != 0:
        img = img.rotate(rotate_angle, expand=True)

    if grayscale:
        img = img.convert("L")

    if contrast != 1.0:
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(contrast)

    if brightness != 1.0:
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(brightness)

    if denoise:
        img = img.filter(ImageFilter.MedianFilter(size=3))

    if sharpen:
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(2.0)

    if not output_path:
        base, ext = os.path.splitext(image_path)
        output_path = f"{base}_processed{ext}"

    img.save(output_path, quality=95)
    return output_path


def create_thumbnail(image_path: str, size: tuple = (300, 400), output_path: Optional[str] = None) -> str:
    img = Image.open(image_path)
    img.thumbnail(size)
    if not output_path:
        base, ext = os.path.splitext(image_path)
        output_path = f"{base}_thumb{ext}"
    img.save(output_path)
    return output_path


def get_image_info(image_path: str) -> dict:
    img = Image.open(image_path)
    return {
        "width": img.width,
        "height": img.height,
        "format": img.format,
        "mode": img.mode,
        "size_bytes": os.path.getsize(image_path),
    }


def batch_preprocess(
    image_paths: List[str],
    output_dir: str,
    grayscale: bool = False,
    denoise: bool = False,
    sharpen: bool = True,
    contrast: float = 1.2,
    brightness: float = 1.0,
) -> List[str]:
    os.makedirs(output_dir, exist_ok=True)
    processed_paths = []
    for path in image_paths:
        filename = os.path.basename(path)
        output_path = os.path.join(output_dir, filename)
        try:
            preprocess_image(
                path,
                grayscale=grayscale,
                denoise=denoise,
                sharpen=sharpen,
                contrast=contrast,
                brightness=brightness,
                output_path=output_path,
            )
            processed_paths.append(output_path)
        except Exception as e:
            print(f"预处理失败 {path}: {e}")
    return processed_paths
