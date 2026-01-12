#!/usr/bin/env python3
"""Generate OG preview image and favicons for GSAU.gg"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import struct
import io

# Paths
STATIC_DIR = Path(__file__).parent.parent / "static"

# Brand colors
GREEN = "#16a34a"  # Theme color
WHITE = "#ffffff"
DARK_BG = "#2a2d30"  # Dark charcoal background


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def create_gradient(width: int, height: int, color1: str, color2: str) -> Image.Image:
    """Create a vertical gradient image."""
    img = Image.new("RGB", (width, height))
    c1 = hex_to_rgb(color1)
    c2 = hex_to_rgb(color2)

    for y in range(height):
        ratio = y / height
        r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
        g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
        b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
        for x in range(width):
            img.putpixel((x, y), (r, g, b))

    return img


def create_og_image():
    """Create the 1200x630 OG preview image with Gelsoft AU branding."""
    width, height = 1200, 630
    img = Image.new("RGB", (width, height), hex_to_rgb(DARK_BG))
    draw = ImageDraw.Draw(img)

    # Load fonts
    try:
        brand_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 120)
        site_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
    except OSError:
        try:
            brand_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
            site_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        except OSError:
            brand_font = ImageFont.load_default()
            site_font = ImageFont.load_default()

    # Draw stacked GEL/SOFT/AU centered in green
    line_height = 110
    start_y = 120

    for i, text in enumerate(["GEL", "SOFT", "AU"]):
        bbox = draw.textbbox((0, 0), text, font=brand_font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        draw.text((x, start_y + i * line_height), text, fill=GREEN, font=brand_font)

    # Draw "GSAU.gg" below
    site_text = "GSAU.gg"
    site_bbox = draw.textbbox((0, 0), site_text, font=site_font)
    site_width = site_bbox[2] - site_bbox[0]
    site_x = (width - site_width) // 2
    draw.text((site_x, 480), site_text, fill=GREEN, font=site_font)

    output_path = STATIC_DIR / "og-default.png"
    img.save(output_path, "PNG")
    print(f"Created: {output_path}")


def create_favicon_base(size: int) -> Image.Image:
    """Create a square favicon with Gelsoft AU branding (dark bg, stacked text)."""
    # Add padding/rounding effect by using slightly larger canvas
    img = Image.new("RGBA", (size, size), hex_to_rgb(DARK_BG) + (255,))
    draw = ImageDraw.Draw(img)

    # For very small sizes, just use "G" in teal
    if size <= 32:
        try:
            font_size = int(size * 0.7)
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except OSError:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except OSError:
                font = ImageFont.load_default()

        letter = "G"
        bbox = draw.textbbox((0, 0), letter, font=font)
        letter_width = bbox[2] - bbox[0]
        letter_height = bbox[3] - bbox[1]
        x = (size - letter_width) // 2
        y = (size - letter_height) // 2 - bbox[1]
        draw.text((x, y), letter, fill=GREEN, font=font)
    else:
        # For larger sizes, use stacked GEL/SOFT/AU
        try:
            font_size = int(size * 0.22)
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except OSError:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except OSError:
                font = ImageFont.load_default()

        line_height = int(size * 0.25)
        start_y = int(size * 0.15)

        # Draw GEL/SOFT/AU in green
        for i, text in enumerate(["GEL", "SOFT", "AU"]):
            bbox = draw.textbbox((0, 0), text, font=font)
            x = (size - (bbox[2] - bbox[0])) // 2
            draw.text((x, start_y + line_height * i), text, fill=GREEN, font=font)

    return img


def create_ico(images: list[Image.Image], output_path: Path):
    """Create an ICO file from multiple PIL Images."""
    # ICO format header
    ico_data = io.BytesIO()

    # ICONDIR structure
    num_images = len(images)
    ico_data.write(struct.pack("<HHH", 0, 1, num_images))  # Reserved, Type (1=ICO), Count

    # Calculate offset for image data (header + directory entries)
    data_offset = 6 + (16 * num_images)

    image_data_list = []

    for img in images:
        # Convert to PNG data
        png_data = io.BytesIO()
        img.save(png_data, "PNG")
        png_bytes = png_data.getvalue()
        image_data_list.append(png_bytes)

        # ICONDIRENTRY structure
        width = img.width if img.width < 256 else 0
        height = img.height if img.height < 256 else 0
        ico_data.write(struct.pack(
            "<BBBBHHII",
            width,          # Width
            height,         # Height
            0,              # Color palette
            0,              # Reserved
            1,              # Color planes
            32,             # Bits per pixel
            len(png_bytes), # Size of image data
            data_offset     # Offset to image data
        ))
        data_offset += len(png_bytes)

    # Write image data
    for png_bytes in image_data_list:
        ico_data.write(png_bytes)

    # Save ICO file
    output_path.write_bytes(ico_data.getvalue())
    print(f"Created: {output_path}")


def create_favicons():
    """Create all favicon sizes."""
    sizes = {
        "favicon-16x16.png": 16,
        "favicon-32x32.png": 32,
        "favicon-192x192.png": 192,
        "favicon-512x512.png": 512,
        "apple-touch-icon.png": 180,
    }

    ico_images = []

    for filename, size in sizes.items():
        img = create_favicon_base(size)
        output_path = STATIC_DIR / filename
        img.save(output_path, "PNG")
        print(f"Created: {output_path}")

        # Collect images for ICO file
        if size in [16, 32, 48]:
            ico_images.append(img)

    # Create 48x48 for ICO
    ico_images.append(create_favicon_base(48))

    # Create favicon.ico with multiple sizes
    create_ico(ico_images, STATIC_DIR / "favicon.ico")


def main():
    """Generate all images."""
    print("Generating OG preview image...")
    create_og_image()

    print("\nGenerating favicons...")
    create_favicons()

    print("\nDone!")


if __name__ == "__main__":
    main()
