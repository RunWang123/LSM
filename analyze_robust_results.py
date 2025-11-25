#!/usr/bin/env python3
"""Analyze results from robust COLMAP batch processing"""

import os
import sys
sys.path.insert(0, '/home/runw/Project/feature-3dgs/scene')
from colmap_loader import read_extrinsics_binary

robust_dir = '/home/runw/Project/LSM/data/scannet_test_colmap_robust'
original_dir = '/home/runw/Project/data/colmap/data/scannet_test_feature3dgs'

print("=" * 80)
print("ROBUST COLMAP Results Analysis")
print("=" * 80)

if not os.path.exists(robust_dir):
    print("Robust output directory not found. Processing may not be complete.")
    sys.exit(1)

scenes = sorted([d for d in os.listdir(robust_dir) if d.startswith('scene')])
print(f"\nTotal scenes processed: {len(scenes)}\n")

good_scenes = []
improved_scenes = []
same_scenes = []
worse_scenes = []
failed_scenes = []

for scene in scenes:
    robust_path = f'{robust_dir}/{scene}/sparse/0/images.bin'
    original_path = f'{original_dir}/{scene}/sparse/0/images.bin'
    
    robust_count = 0
    original_count = 0
    
    if os.path.exists(robust_path):
        robust_extr = read_extrinsics_binary(robust_path)
        robust_count = len(robust_extr)
    
    if os.path.exists(original_path):
        original_extr = read_extrinsics_binary(original_path)
        original_count = len(original_extr)
    
    if robust_count == 0:
        failed_scenes.append((scene, original_count, robust_count))
    elif robust_count >= 25:
        good_scenes.append((scene, original_count, robust_count))
        if robust_count > original_count:
            improved_scenes.append((scene, original_count, robust_count))
    elif robust_count > original_count:
        improved_scenes.append((scene, original_count, robust_count))
    elif robust_count == original_count:
        same_scenes.append((scene, original_count, robust_count))
    else:
        worse_scenes.append((scene, original_count, robust_count))

print(f"📊 Summary:")
print(f"  ✅ Good scenes (25+ frames): {len(good_scenes)}")
print(f"  📈 Improved (but <25 frames): {len(improved_scenes) - len([s for s in improved_scenes if s[2] >= 25])}")
print(f"  → Same as before: {len(same_scenes)}")
print(f"  📉 Got worse: {len(worse_scenes)}")
print(f"  ❌ Failed (0 frames): {len(failed_scenes)}")

if good_scenes:
    print(f"\n✅ Good scenes (25+ frames) - {len(good_scenes)} scenes:")
    for scene, orig, robust in sorted(good_scenes, key=lambda x: x[2], reverse=True):
        change = f" (was {orig})" if orig != robust else ""
        print(f"  {scene}: {robust} frames{change}")

if improved_scenes:
    print(f"\n📈 Improved scenes:")
    for scene, orig, robust in sorted(improved_scenes, key=lambda x: x[2] - x[1], reverse=True):
        if robust >= 25:
            continue  # Already shown above
        print(f"  {scene}: {orig} → {robust} frames")

if worse_scenes:
    print(f"\n📉 Got worse:")
    for scene, orig, robust in worse_scenes[:10]:
        print(f"  {scene}: {orig} → {robust} frames")

# Save good scenes list
good_scene_names = [s[0] for s in good_scenes]
with open('/home/runw/Project/feature-3dgs/good_scenes_robust.txt', 'w') as f:
    for scene in sorted(good_scene_names):
        f.write(f"{scene}\n")

print(f"\n💾 Good scenes list saved to: /home/runw/Project/feature-3dgs/good_scenes_robust.txt")
print(f"   Total: {len(good_scene_names)} scenes with 25+ frames")

