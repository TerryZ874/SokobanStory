#!/usr/bin/env python3
"""Score all small-pool levels and write to data/pools/scored_levels.json"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.campaign_builder import score_level, CACHE_FILE, load_all_pool_levels

LOG = "data/pools/scoring_log.txt"
log_fh = open(LOG, "w", buffering=1)

def log(msg):
    print(msg)
    log_fh.write(msg + "\n")

log("Loading levels...")
all_levels = load_all_pool_levels(max_boxes=15)
log(f"\nTotal: {len(all_levels)} levels")

scored = []
t0 = time.time()
for i, lv in enumerate(all_levels):
    s = score_level(lv)
    s["pool_idx"] = i
    scored.append(s)

    if i % 500 == 0 and i > 0:
        dt = time.time() - t0
        rate = i / dt
        log(f"  [{i}/{len(all_levels)}] {rate:.0f}/s, {dt:.0f}s elapsed")

log(f"\nSaving to {CACHE_FILE}...")
with open(CACHE_FILE, "w") as f:
    json.dump(scored, f)

dt = time.time() - t0
bfs_ok = sum(1 for s in scored if s["bfs_steps"] is not None)
log(f"\nDone: {len(scored)} levels in {dt:.0f}s")
log(f"BFS solved: {bfs_ok}")
log(f"Heuristic: {len(scored) - bfs_ok}")
log_fh.close()
