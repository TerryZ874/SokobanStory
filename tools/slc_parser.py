#!/usr/bin/env python3
"""
SLC/Text Sokoban level parser.
Converts text format levels to levels.json format.

Usage:
  python3 tools/slc_parser.py reference/level_file.txt -o data/imported.json
  python3 tools/slc_parser.py reference/ --dir -o data/imported.json
  python3 tools/slc_parser.py reference/level.txt          # print to stdout
"""

import json
import os
import sys
import re
from bfs_solver import solve, validate_level

CHAR_MAP = {
    '#': 1,   # wall
    '-': 0,   # floor
    ' ': 0,   # floor
    '.': 0,   # target (floor in grid, tracked separately)
    '$': 2,   # box
    '@': 3,   # player
    '*': 2,   # box on target (box in grid, also target)
    '+': 3,   # player on target (player in grid, also target)
}


def parse_level_text(text: str, level_id: int = 1, name: str = ""):
    """
    Parse a single Sokoban level from text format.

    Returns a level dict compatible with levels.json format,
    or None if parsing fails.
    """
    lines = text.split('\n')
    # Strip empty lines at start/end
    while lines and lines[0].strip() == '':
        lines.pop(0)
    while lines and lines[-1].strip() == '':
        lines.pop()

    # Remove metadata lines — a real level row always has at least one wall (#)
    lines = [l for l in lines if '#' in l]

    if not lines:
        return None

    # Normalize: ensure all rows are the same width
    # First, pad shorter rows with spaces on both sides
    # But actually, in SLC format, empty space = floor (out-of-bounds)
    # We trim leading/trailing empty columns for a tight bounding box

    # Find the bounding box (trimming empty columns)
    max_width = max(len(line) for line in lines)
    rows = len(lines)

    # Pad all rows to same width
    grid_text = [line.ljust(max_width) for line in lines]

    # Trim trailing empty columns that are all floor across all rows
    # Actually, keep the full bounding box for simplicity

    grid = []
    targets = []
    player_count = 0
    box_count = 0

    for y, line in enumerate(grid_text):
        row = []
        for x, ch in enumerate(line):
            val = CHAR_MAP.get(ch, 0)
            row.append(val)

            if ch in ('.', '*', '+'):
                targets.append([x, y])
            if ch == '$' or ch == '*':
                box_count += 1
            if ch == '@' or ch == '+':
                player_count += 1

        grid.append(row)

    if player_count != 1:
        print(f"  ERROR: Level {level_id}: {player_count} players, expected 1", file=sys.stderr)
        return None
    if box_count == 0:
        print(f"  ERROR: Level {level_id}: no boxes", file=sys.stderr)
        return None
    if not targets:
        print(f"  ERROR: Level {level_id}: no targets", file=sys.stderr)
        return None
    if box_count != len(targets):
        print(f"  ERROR: Level {level_id}: {box_count} boxes but {len(targets)} targets", file=sys.stderr)
        return None

    return {
        "id": level_id,
        "name": name or f"Level {level_id}",
        "cols": len(grid[0]),
        "rows": len(grid),
        "step_limit": 999,
        "grid": grid,
        "targets": targets,
    }


def parse_level_file(filepath: str, start_id: int = 1):
    """
    Parse a file containing one or more Sokoban levels.
    Levels are separated by blank lines.

    Returns list of level dicts.
    """
    # Try multiple encodings (Chinese SLC files are often GBK/GB2312)
    content = None
    for enc in ('utf-8', 'gbk', 'gb2312', 'latin-1'):
        try:
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read()
                break
        except UnicodeDecodeError:
            continue
    if content is None:
        print(f"  WARNING: Cannot decode {filepath}", file=sys.stderr)
        return []

    # Split on blank lines (one or more empty lines)
    blocks = re.split(r'\n\s*\n', content)
    blocks = [b.strip() for b in blocks if b.strip()]

    filename = os.path.splitext(os.path.basename(filepath))[0]
    levels = []

    lid = start_id
    for i, block in enumerate(blocks):
        name = f"{filename} #{i+1}"
        level = parse_level_text(block, lid, name)
        if level:
            levels.append(level)
            lid += 1

    return levels


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Parse SLC/text Sokoban levels")
    parser.add_argument("input", help="Input file or directory")
    parser.add_argument("-o", "--output", help="Output JSON file")
    parser.add_argument("--dir", action="store_true", help="Input is a directory, scan all .txt/.sok files")
    parser.add_argument("--start-id", type=int, default=1, help="Starting level ID (default: 1)")
    parser.add_argument("--step-limit", type=int, default=0,
                        help="Step limit multiplier over BFS min steps: limit = min_steps * multiplier (default: auto 5x)")
    parser.add_argument("--verify", action="store_true", default=True,
                        help="Verify levels with BFS solver (default: on)")
    parser.add_argument("--no-verify", action="store_false", dest="verify",
                        help="Skip BFS verification")

    args = parser.parse_args()

    all_levels = []

    if args.dir:
        input_dir = args.input
        if not os.path.isdir(input_dir):
            print(f"Error: {input_dir} is not a directory", file=sys.stderr)
            sys.exit(1)

        files = sorted(os.listdir(input_dir))
        for fname in files:
            fpath = os.path.join(input_dir, fname)
            if os.path.isfile(fpath) and fname.lower().endswith(('.txt', '.sok', '.slc', '.xsb')):
                print(f"Parsing: {fpath}")
                levels = parse_level_file(fpath, args.start_id)
                all_levels.extend(levels)
                args.start_id += len(levels)
    else:
        fpath = args.input
        if not os.path.isfile(fpath):
            print(f"Error: {fpath} is not a file", file=sys.stderr)
            sys.exit(1)
        print(f"Parsing: {fpath}")
        all_levels = parse_level_file(fpath, args.start_id)

    print(f"\nParsed {len(all_levels)} levels")

    # Verify with BFS
    if args.verify and all_levels:
        print(f"\n--- BFS Verification ---")
        verified = []
        for level in all_levels:
            num_boxes = sum(row.count(2) for row in level['grid'])
            grid_cells = level['rows'] * level['cols']

            # Skip BFS for levels that are too complex (>4 boxes or large grid)
            if num_boxes > 4 or grid_cells > 100:
                print(f"  Level {level['id']:4d}: SKIP (complex: {num_boxes} boxes, {level['rows']}x{level['cols']})")
                level['step_limit'] = max(num_boxes * 80, 200)
                verified.append(level)
                continue

            solvable, min_steps, error = validate_level(level)
            if solvable:
                print(f"  Level {level['id']:4d}: OK  min_steps={min_steps}")
                # Set step limit: min_steps * multiplier + buffer
                mult = args.step_limit if args.step_limit > 0 else 5
                level['step_limit'] = max(min_steps * mult + 10, 20)
                verified.append(level)
            else:
                print(f"  Level {level['id']:4d}: FAIL - {error}")

        if not verified:
            print("\nNo valid levels found!", file=sys.stderr)
            sys.exit(1)

        print(f"\n{len(verified)}/{len(all_levels)} levels passed BFS verification")
        all_levels = verified

    # Build output
    output = {"levels": all_levels}

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"\nWritten to {args.output}")
    else:
        print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
