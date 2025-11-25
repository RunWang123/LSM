#!/usr/bin/env python3
"""
Modified COLMAP script for ScanNet test dataset.
- Uses SIMPLE_RADIAL camera model (for preprocessed 448x448 images)
- Skips undistortion (keeps images as-is)
- Only generates camera poses and sparse 3D points
"""

import os
import logging
from argparse import ArgumentParser
import shutil

# Set environment for headless COLMAP (no GUI)
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

parser = ArgumentParser("COLMAP for ScanNet preprocessed images")
parser.add_argument("--no_gpu", action='store_true', help="Disable GPU")
parser.add_argument("--scene", type=str, required=True, help="Scene name (e.g., scene0686_01)")
parser.add_argument("--source_path", "-s", type=str, 
                    default="/home/runw/Project/data/colmap/data/scannet_test_preprocessed",
                    help="Root path containing preprocessed scenes")
parser.add_argument("--output_path", "-o", type=str,
                    default="/home/runw/Project/LSM/data/scannet_test_colmap",
                    help="Output path for COLMAP results")
parser.add_argument("--camera", default="SIMPLE_RADIAL", type=str,
                    help="Camera model (SIMPLE_RADIAL for preprocessed images)")
parser.add_argument("--colmap_executable", default="colmap", type=str)
args = parser.parse_args()

colmap_command = '"{}"'.format(args.colmap_executable) if len(args.colmap_executable) > 0 else "colmap"
use_gpu = 1 if not args.no_gpu else 0

# Set up paths
scene_input = os.path.join(args.source_path, args.scene, "color")
scene_output = os.path.join(args.output_path, args.scene)

# Check if scene exists
if not os.path.isdir(scene_input):
    logging.error(f"Scene {args.scene} not found at {scene_input}")
    exit(1)

# Create output directories
os.makedirs(scene_output, exist_ok=True)
os.makedirs(os.path.join(scene_output, "sparse"), exist_ok=True)

print(f"Processing scene: {args.scene}")
print(f"Input images: {scene_input}")
print(f"Output path: {scene_output}")
print(f"Camera model: {args.camera}")
print()

## Feature extraction
print("Step 1/3: Feature extraction...")
feat_extraction_cmd = colmap_command + f''' feature_extractor \
    --database_path {scene_output}/database.db \
    --image_path {scene_input} \
    --ImageReader.single_camera 1 \
    --ImageReader.camera_model {args.camera} \
    --SiftExtraction.use_gpu {use_gpu}'''

exit_code = os.system(feat_extraction_cmd)
if exit_code != 0:
    logging.error(f"Feature extraction failed with code {exit_code}. Exiting.")
    exit(exit_code)

## Feature matching
print("Step 2/3: Feature matching...")
feat_matching_cmd = colmap_command + f''' exhaustive_matcher \
    --database_path {scene_output}/database.db \
    --SiftMatching.use_gpu {use_gpu}'''

exit_code = os.system(feat_matching_cmd)
if exit_code != 0:
    logging.error(f"Feature matching failed with code {exit_code}. Exiting.")
    exit(exit_code)

## Mapping (Bundle Adjustment)
print("Step 3/3: Sparse reconstruction (mapper)...")
mapper_cmd = colmap_command + f''' mapper \
    --database_path {scene_output}/database.db \
    --image_path {scene_input} \
    --output_path {scene_output}/sparse \
    --Mapper.ba_global_function_tolerance=0.000001'''

exit_code = os.system(mapper_cmd)
if exit_code != 0:
    logging.error(f"Mapper failed with code {exit_code}. Exiting.")
    exit(exit_code)

# Organize output (move to sparse/0 if not already there)
files = os.listdir(os.path.join(scene_output, "sparse"))
if '0' not in files:
    # If mapper created files directly in sparse/, create sparse/0 and move them
    os.makedirs(os.path.join(scene_output, "sparse", "0"), exist_ok=True)
    for file in files:
        if file == '0':
            continue
        source_file = os.path.join(scene_output, "sparse", file)
        destination_file = os.path.join(scene_output, "sparse", "0", file)
        if os.path.isfile(source_file):
            shutil.move(source_file, destination_file)

print()
print("=" * 60)
print(f"COLMAP reconstruction complete for {args.scene}!")
print(f"Output saved to: {scene_output}/sparse/0/")
print(f"  - cameras.bin (camera parameters)")
print(f"  - images.bin (camera poses)")
print(f"  - points3D.bin (sparse 3D points)")
print("=" * 60)
print()
print("NOTE: Images were NOT modified (no undistortion applied)")
print("      Using preprocessed 448x448 images as-is")

