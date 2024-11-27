import base64
import io
import re

from PIL import Image
from io import BytesIO


def get_image_dimensions(b64_string: str) -> tuple[int, int]:
    """
    Get the dimensions of a base64-encoded image.
    """
    image_data = base64.b64decode(b64_string)
    image = Image.open(BytesIO(image_data))
    return image.size


def get_image_format(b64_string: str) -> str:
    """
    Get the format of a base64-encoded image.
    """
    image_data = base64.b64decode(b64_string)
    image = Image.open(BytesIO(image_data))
    return image.format.lower()


def looks_like_base64(sb: str) -> bool:
    """Check if the string looks like base64"""
    return re.match("^[A-Za-z0-9+/]+[=]{0,2}$", sb) is not None


def is_image_data(b64data: str) -> bool:
    """
    Check if the base64 data is an image by looking at the start of the data
    """
    image_signatures = {
        b"\xff\xd8\xff": "jpg",
        b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a": "png",
        b"\x47\x49\x46\x38": "gif",
        b"\x52\x49\x46\x46": "webp",
    }
    try:
        header = base64.b64decode(b64data)[:8]  # Decode and get the first 8 bytes
        for sig, _format in image_signatures.items():
            if header.startswith(sig):
                return True
        return False
    except Exception:
        return False


def resize_base64_image(
    base64_string: str, size: tuple[int, int] = (128, 128)
) -> tuple[bytes, str]:
    """
    Resize an image encoded as a Base64 string and print the previous size.
    """
    # Decode the Base64 string
    img_data = base64.b64decode(base64_string)
    img = Image.open(io.BytesIO(img_data))
    # Get the previous size
    previous_size = img.size
    print(f"Previous size: {previous_size}")
    print(f"Resizing image to size {size}")

    # Resize the image
    resized_img = img.resize(size, Image.Resampling.LANCZOS)

    # Save the resized image to a bytes buffer
    buffered = io.BytesIO()
    resized_img.save(buffered, format=img.format)

    # Encode the resized image to Base64
    buf = buffered.getvalue()
    return buf, base64.b64encode(buf).decode("utf-8")
