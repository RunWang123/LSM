#!/usr/bin/env python3
"""
Modified COLMAP script for ScanNet test dataset with ROBUST settings.
- More lenient matching thresholds
- Sequential matcher instead of exhaustive
- Lower BA tolerance
"""

import os
import logging
from argparse import ArgumentParser
import shutil

os.environ['QT_QPA_PLATFORM'] = 'offscreen'

parser = ArgumentParser("COLMAP for ScanNet preprocessed images")
parser.add_argument("--no_gpu", action='store_true', help="Disable GPU")
parser.add_argument("--scene", type=str, required=True, help="Scene name")
parser.add_argument("--source_path", "-s", type=str, 
                    default="/home/runw/Project/data/colmap/data/scannet_test_preprocessed")
parser.add_argument("--output_path", "-o", type=str,
                    default="/home/runw/Project/LSM/data/scannet_test_colmap_robust")
parser.add_argument("--camera", default="SIMPLE_RADIAL", type=str)
parser.add_argument("--colmap_executable", default="colmap", type=str)
args = parser.parse_args()

colmap_command = '"{}"'.format(args.colmap_executable) if len(args.colmap_executable) > 0 else "colmap"
use_gpu = 1 if not args.no_gpu else 0

scene_input = os.path.join(args.source_path, args.scene, "color")
scene_output = os.path.join(args.output_path, args.scene)

if not os.path.isdir(scene_input):
    logging.error(f"Scene {args.scene} not found at {scene_input}")
    exit(1)

os.makedirs(scene_output, exist_ok=True)
os.makedirs(os.path.join(scene_output, "sparse"), exist_ok=True)

print(f"Processing scene: {args.scene} (ROBUST MODE)")
print(f"Input images: {scene_input}")
print(f"Output path: {scene_output}")
print()

## Feature extraction (MORE features)
print("Step 1/4: Feature extraction (robust mode)...")
feat_extraction_cmd = colmap_command + f''' feature_extractor \
    --database_path {scene_output}/database.db \
    --image_path {scene_input} \
    --ImageReader.single_camera 1 \
    --ImageReader.camera_model {args.camera} \
    --SiftExtraction.use_gpu {use_gpu} \
    --SiftExtraction.max_num_features 16384 \
    --SiftExtraction.first_octave -1'''

exit_code = os.system(feat_extraction_cmd)
if exit_code != 0:
    logging.error(f"Feature extraction failed. Exiting.")
    exit(exit_code)

## Sequential matching (better for video-like sequences)
print("Step 2/4: Sequential matching...")
seq_matching_cmd = colmap_command + f''' sequential_matcher \
    --database_path {scene_output}/database.db \
    --SiftMatching.use_gpu {use_gpu} \
    --SequentialMatching.overlap 15 \
    --SequentialMatching.loop_detection 0'''

exit_code = os.system(seq_matching_cmd)
if exit_code != 0:
    logging.warning(f"Sequential matching failed with code {exit_code}. Trying exhaustive...")

## Also try exhaustive for safety (or as fallback)
print("Step 3/4: Exhaustive matching...")
exh_matching_cmd = colmap_command + f''' exhaustive_matcher \
    --database_path {scene_output}/database.db \
    --SiftMatching.use_gpu {use_gpu}'''

exit_code_exh = os.system(exh_matching_cmd)
if exit_code_exh != 0 and exit_code != 0:
    logging.error(f"Both sequential and exhaustive matching failed. Cannot proceed.")
    exit(1)

## Mapping with lenient parameters
print("Step 4/4: Sparse reconstruction (lenient mode)...")
mapper_cmd = colmap_command + f''' mapper \
    --database_path {scene_output}/database.db \
    --image_path {scene_input} \
    --output_path {scene_output}/sparse \
    --Mapper.ba_global_function_tolerance=0.00001 \
    --Mapper.min_num_matches=10 \
    --Mapper.init_min_num_inliers=50 \
    --Mapper.abs_pose_min_num_inliers=10'''

exit_code = os.system(mapper_cmd)
if exit_code != 0:
    logging.warning(f"Mapper returned non-zero exit code {exit_code}")

# Organize output
sparse_dir = os.path.join(scene_output, "sparse")
files = os.listdir(sparse_dir) if os.path.exists(sparse_dir) else []

if '0' not in files and len(files) > 0:
    # Mapper created files directly in sparse/, move to sparse/0
    os.makedirs(os.path.join(sparse_dir, "0"), exist_ok=True)
    for file in files:
        if file == '0':
            continue
        source_file = os.path.join(sparse_dir, file)
        destination_file = os.path.join(sparse_dir, "0", file)
        if os.path.isfile(source_file):
            shutil.move(source_file, destination_file)

# Check if reconstruction succeeded
images_bin_path = os.path.join(sparse_dir, "0", "images.bin")
if os.path.exists(images_bin_path):
    # Count registered images
    import sys
    sys.path.append('/home/runw/Project/feature-3dgs/scene')
    from colmap_loader import read_extrinsics_binary
    
    extrinsics = read_extrinsics_binary(images_bin_path)
    num_registered = len(extrinsics)
    
    print()
    print("=" * 60)
    print(f"✅ COLMAP reconstruction complete for {args.scene}!")
    print(f"Registered {num_registered} images")
    print(f"Output: {scene_output}/sparse/0/")
    print("=" * 60)
else:
    print()
    print("=" * 60)
    print(f"❌ COLMAP reconstruction FAILED for {args.scene}")
    print(f"Mapper could not register any images.")
    print(f"This scene may have:")
    print(f"  - Insufficient texture/features")
    print(f"  - Too few overlapping views")
    print(f"  - Poor image quality")
    print("=" * 60)
    exit(1)

