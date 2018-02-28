import numpy as np
import PIL.Image
import PIL.ImageDraw
import io

def mask_image(original_image, masked_image):
    cam_img_arr = np.asarray(original_image, dtype=np.uint8)
    mask_img_arr = np.asarray(masked_image, dtype=np.uint8)
    masked_cam_array = cam_img_arr * np.dstack([np.where(mask_img_arr > 0, 1, 0)] * 3).astype(np.uint8)
    masked_cam_image = PIL.Image.fromarray(masked_cam_array)
    img_output = io.BytesIO()
    masked_cam_image.save(img_output, format='JPEG')
    return img_output.getvalue()


def create_mask_image(x1, y1, x2, y2):
    mask_image = PIL.Image.new("1", (1920, 1080))
    draw = PIL.ImageDraw.Draw(mask_image)
    draw.rectangle([x1, y1, x2, y2], fill=1)
    img_output = io.BytesIO()
    mask_image.save(img_output, format='JPEG')
    return img_output.getvalue()