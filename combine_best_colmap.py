#!/usr/bin/env python3
"""Combine best COLMAP results from original and robust runs"""

import os
import sys
import shutil
sys.path.insert(0, '/home/runw/Project/feature-3dgs/scene')
from colmap_loader import read_extrinsics_binary

# Paths
original_dir = '/home/runw/Project/data/colmap/data/scannet_test_feature3dgs'
robust_dir = '/home/runw/Project/LSM/data/scannet_test_colmap_robust'
best_dir = '/home/runw/Project/data/colmap/data/scannet_test_feature3dgs_BEST_COMBINED'

print("=" * 80)
print("Combining BEST COLMAP Results (Original + Robust)")
print("=" * 80)

# Get all scenes
scenes = sorted([d for d in os.listdir(robust_dir) if d.startswith('scene')])
print(f"\nProcessing {len(scenes)} scenes...\n")

os.makedirs(best_dir, exist_ok=True)

good_scenes = []
used_original = 0
used_robust = 0

for scene in scenes:
    orig_path = f'{original_dir}/{scene}/sparse/0/images.bin'
    robust_path = f'{robust_dir}/{scene}/sparse/0/images.bin'
    
    orig_count = 0
    robust_count = 0
    
    # Count frames in original
    if os.path.exists(orig_path):
        orig_extr = read_extrinsics_binary(orig_path)
        orig_count = len(orig_extr)
    
    # Count frames in robust
    if os.path.exists(robust_path):
        robust_extr = read_extrinsics_binary(robust_path)
        robust_count = len(robust_extr)
    
    # Choose the better one
    if orig_count >= robust_count:
        source = original_dir
        count = orig_count
        choice = "ORIG"
        used_original += 1
    else:
        source = robust_dir
        count = robust_count
        choice = "ROBUST"
        used_robust += 1
    
    # Determine quality
    if count >= 25:
        status = "✅ GOOD"
        good_scenes.append(scene)
    elif count >= 15:
        status = "⚠️  OK"
    else:
        status = "❌ BAD"
    
    print(f"{scene}: {count} frames ({choice:6s}) {status}")
    
    # Copy the better result
    src_scene_dir = f'{source}/{scene}'
    dst_scene_dir = f'{best_dir}/{scene}'
    
    if os.path.exists(src_scene_dir):
        if os.path.exists(dst_scene_dir):
            shutil.rmtree(dst_scene_dir)
        shutil.copytree(src_scene_dir, dst_scene_dir)

print()
print("=" * 80)
print(f"\n📊 Summary:")
print(f"  Used original: {used_original}")
print(f"  Used robust: {used_robust}")
print(f"  ✅ Good scenes (25+ frames): {len(good_scenes)}")

# Save good scenes list
good_scenes_file = '/home/runw/Project/feature-3dgs/good_scenes_combined.txt'
with open(good_scenes_file, 'w') as f:
    for scene in sorted(good_scenes):
        f.write(f"{scene}\n")

print(f"\n💾 Results saved to: {best_dir}")
print(f"💾 Good scenes list: {good_scenes_file}")
print(f"\nTotal good scenes: {len(good_scenes)}")

