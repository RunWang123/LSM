#!/usr/bin/env python3
"""
Preprocessing script for ScanNet test dataset - IMAGES ONLY
Uses LSM's resize logic but only saves images (no intrinsics/poses).
No need to skip invalid poses since we're not using them.
"""

import os
import numpy as np
import argparse
from tqdm import tqdm
import json
import torch
import cv2


def resize_and_crop_images(color_data, depth_data, target_height=448, target_width=448, device='cpu'):
    """
    Resize and center crop using EXACT same logic as LSM (base_processor.py lines 91-113).
    But only return images, no intrinsics adjustment.
    
    Args:
        color_data: numpy array (H, W, 3)
        depth_data: numpy array (H, W)
        target_height: target height after processing
        target_width: target width after processing
        device: torch device
    
    Returns:
        Tuple of (processed_image, processed_depth)
    """
    # Convert to torch tensors (same as LSM)
    color_data = torch.from_numpy(color_data.astype(np.float32)).to(device)
    depth_data = torch.from_numpy(depth_data.astype(np.float32)).to(device)
    
    # Add batch dimension
    color_data = color_data.unsqueeze(0)  # (1, H, W, 3)
    depth_data = depth_data.unsqueeze(0)  # (1, H, W)
    
    # Get original dimensions (EXACT same as LSM line 92)
    batch_size, original_h, original_w = depth_data.shape
    
    # Calculate resize ratio (EXACT same as LSM lines 93-95)
    h_ratio = target_height / original_h
    w_ratio = target_width / original_w
    ratio = max(h_ratio, w_ratio)
    new_h, new_w = int(original_h * ratio), int(original_w * ratio)
    
    # Ensure dimensions are at least target size (handle rounding)
    if new_h < target_height:
        new_h = target_height
    if new_w < target_width:
        new_w = target_width
    
    # Calculate crop offsets (same as LSM lines 102-103)
    start_x = (new_w - target_width) // 2
    start_y = (new_h - target_height) // 2
    
    # Resize images (EXACT same as LSM lines 107-109)
    depth_data = torch.nn.functional.interpolate(depth_data.unsqueeze(1), size=(new_h, new_w), mode='nearest')
    color_data = torch.nn.functional.interpolate(color_data.permute(0, 3, 1, 2), size=(new_h, new_w), mode='bilinear')
    
    # Crop images (EXACT same as LSM lines 111-113)
    depth_data = depth_data[:, :, start_y:start_y + target_height, start_x:start_x + target_width]
    color_data = color_data[:, :, start_y:start_y + target_height, start_x:start_x + target_width]
    
    # Convert back to numpy (remove batch dimension)
    color_data = color_data[0].permute(1, 2, 0).cpu().numpy()
    depth_data = depth_data[0, 0].cpu().numpy()
    
    return color_data, depth_data


def process_scene(scene_path, output_path, selected_frames, target_height=448, target_width=448, device='cpu'):
    """
    Process a single scene - IMAGES ONLY (no intrinsics/poses).
    Only processes frames specified in selected_seqs_test.json (30 frames per scene).
    
    Args:
        scene_path: path to the scene folder
        output_path: path to save processed scene
        selected_frames: list of frame IDs to process (from JSON)
        target_height: target height for processed images
        target_width: target width for processed images
        device: torch device
    """
    scene_name = os.path.basename(scene_path)
    
    # Create output directories
    output_scene_path = os.path.join(output_path, scene_name)
    os.makedirs(os.path.join(output_scene_path, 'color'), exist_ok=True)
    os.makedirs(os.path.join(output_scene_path, 'depth'), exist_ok=True)
    
    # Get directories
    images_dir = os.path.join(scene_path, 'images')
    depths_dir = os.path.join(scene_path, 'depths')
    
    # Use frame IDs from JSON (LSM selects 30 frames per scene)
    frame_ids = selected_frames
    
    processed_count = 0
    
    for frame_id in tqdm(frame_ids, desc=f"Processing {scene_name}"):
        try:
            # Load image using cv2 (same as LSM)
            image_path = os.path.join(images_dir, f'{frame_id}.jpg')
            color_data = cv2.imread(image_path)  # BGR format
            
            # Load depth using cv2 (same as LSM)
            depth_path = os.path.join(depths_dir, f'{frame_id}.png')
            depth_data = cv2.imread(depth_path, cv2.IMREAD_UNCHANGED)
            
            # Process using EXACT same resize logic as LSM
            color_processed, depth_processed = resize_and_crop_images(
                color_data, depth_data, target_height, target_width, device
            )
            
            # Save processed image
            color_save_path = os.path.join(output_scene_path, 'color', f'{frame_id}.png')
            color_processed = color_processed.astype(np.uint8)
            cv2.imwrite(color_save_path, color_processed)
            
            # Save processed depth
            depth_save_path = os.path.join(output_scene_path, 'depth', f'{frame_id}.png')
            depth_processed = depth_processed.astype(np.uint16)
            cv2.imwrite(depth_save_path, depth_processed)
            
            processed_count += 1
            
        except Exception as e:
            print(f"  Error processing {frame_id}: {e}")
            continue
    
    print(f"  Processed {processed_count} frames")
    torch.cuda.empty_cache()
    return processed_count


def main():
    parser = argparse.ArgumentParser(description='Preprocess ScanNet test images using LSM resize logic')
    parser.add_argument('--input_dir', type=str, 
                        default='/home/runw/Project/data/colmap/data/scannet_test',
                        help='Input directory containing test scenes')
    parser.add_argument('--output_dir', type=str,
                        default='/home/runw/Project/LSM/data/scannet_test_images',
                        help='Output directory for processed images')
    parser.add_argument('--target_height', type=int, default=448,
                        help='Target height for processed images')
    parser.add_argument('--target_width', type=int, default=448,
                        help='Target width for processed images')
    parser.add_argument('--scene', type=str, default=None,
                        help='Process only a specific scene (for testing)')
    parser.add_argument('--device', type=str, default='cpu',
                        help='Device to use (cpu or cuda)')
    
    args = parser.parse_args()
    
    # Setup device
    device = torch.device(args.device)
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load selected sequences from JSON (SAME as LSM testdata.py line 36-37)
    json_path = os.path.join(args.input_dir, 'selected_seqs_test.json')
    with open(json_path, 'r') as f:
        selected_seqs = json.load(f)
    
    # Filter scenes if requested
    if args.scene:
        if args.scene in selected_seqs:
            selected_seqs = {args.scene: selected_seqs[args.scene]}
        else:
            print(f"Scene {args.scene} not found in selected_seqs_test.json")
            return
    
    print(f"Found {len(selected_seqs)} scenes to process")
    print(f"Target resolution: {args.target_width}x{args.target_height}")
    print(f"Input directory: {args.input_dir}")
    print(f"Output directory: {args.output_dir}")
    print(f"Mode: IMAGES ONLY (no intrinsics/poses)")
    print(f"Using selected_seqs_test.json (30 frames per scene)")
    print()
    
    total_processed = 0
    
    for scene_name, frame_list in selected_seqs.items():
        scene_path = os.path.join(args.input_dir, scene_name)
        
        # Check if scene exists
        if not os.path.isdir(scene_path):
            print(f"Skipping {scene_name}: scene folder not found")
            continue
        if not os.path.isdir(os.path.join(scene_path, 'images')):
            print(f"Skipping {scene_name}: no images folder")
            continue
        if not os.path.isdir(os.path.join(scene_path, 'depths')):
            print(f"Skipping {scene_name}: no depths folder")
            continue
        
        processed = process_scene(scene_path, args.output_dir, frame_list,
                                  args.target_height, args.target_width, device)
        total_processed += processed
    
    print()
    print("=" * 60)
    print(f"Preprocessing complete!")
    print(f"Total frames processed: {total_processed}")
    print(f"Output saved to: {args.output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()

