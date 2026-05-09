#!/usr/bin/env python3
"""
Convert splash.jpeg to ASCII art.
Uses macOS sips for resizing, parses BMP output.
"""
import subprocess, struct, os

SRC = "reference/splash.jpeg"
WIDTH = 120  # characters wide (wider for better aspect ratio, every 2nd row sampled)

# Custom gradient: user requested @ # * . + and space
# Dark → Light
CHARS = "@#*+. "  # 6 levels, space is brightest background


def read_bmp_grayscale(fpath):
    """Read a 24-bit BMP and return (w, h, grayscale list)."""
    with open(fpath, 'rb') as f:
        data = f.read()

    # BMP header: offset 10 = pixel data start
    pixel_offset = struct.unpack_from('<I', data, 10)[0]
    # DIB header: offset 18 = width, 22 = height
    raw_w = struct.unpack_from('<i', data, 18)[0]
    raw_h = struct.unpack_from('<i', data, 22)[0]
    bpp = struct.unpack_from('<H', data, 28)[0]

    w = abs(raw_w)
    h = abs(raw_h)
    top_down = raw_h < 0

    # BMP stores rows 4-byte aligned
    row_size = ((w * bpp + 31) // 32) * 4

    grayscale = []
    y_range = range(h) if top_down else range(h - 1, -1, -1)
    for y in y_range:
        row_start = pixel_offset + y * row_size
        for x in range(w):
            offset = row_start + x * 3
            b = data[offset]
            g = data[offset + 1]
            r = data[offset + 2]
            gray = int(0.299 * r + 0.587 * g + 0.114 * b)
            grayscale.append(gray)

    return w, h, grayscale


def pixel_to_char(v, maxval=255):
    """Map grayscale value to ASCII char (dark→light)."""
    # Flip: bright bg → space (inverted for dark-on-light look)
    idx = int((maxval - v) / maxval * (len(CHARS) - 1))
    return CHARS[idx]


def main():
    tmp = "/tmp/splash_ascii.bmp"
    subprocess.run([
        "sips", "-s", "format", "bmp",
        "--resampleWidth", str(WIDTH),
        SRC, "--out", tmp
    ], check=True, capture_output=True)

    w, h, pixels = read_bmp_grayscale(tmp)

    # Build ASCII art (skip every 2nd row to fix char aspect ratio)
    lines = []
    for y in range(0, h, 2):
        line = ''.join(pixel_to_char(pixels[y * w + x]) for x in range(w))
        lines.append(line)

    # Preview
    print(f"ASCII art: {w} x {h}")
    for line in lines:
        print(line)

    # Write as GDScript constant
    esc_lines = []
    for line in lines:
        escaped = line.replace("\\", "\\\\").replace('"', '\\"')
        esc_lines.append(escaped)

    gdscript = (
        "# Auto-generated ASCII splash art\n"
        "# Source: reference/splash.jpeg\n\n"
        "const SPLASH_ASCII := \"" + "\\n".join(esc_lines) + "\"\n"
    )

    with open("scripts/ui/splash_ascii.gd", 'w') as f:
        f.write(gdscript)

    print(f"\nWritten to scripts/ui/splash_ascii.gd ({h} lines)")


if __name__ == '__main__':
    main()
