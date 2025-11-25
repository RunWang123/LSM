#!/bin/bash
# Batch script to run COLMAP on all ScanNet test scenes

SOURCE_PATH="/home/runw/Project/data/colmap/data/scannet_test_preprocessed"
OUTPUT_PATH="/home/runw/Project/LSM/data/scannet_test_colmap"

# Get list of scenes
scenes=$(ls "$SOURCE_PATH" | grep "^scene")

total=$(echo "$scenes" | wc -l)
current=0

echo "Found $total scenes to process"
echo "================================"
echo

for scene in $scenes; do
    current=$((current + 1))
    echo "[$current/$total] Processing $scene..."
    
    python /home/runw/Project/LSM/colmap_scannet_test.py \
        --scene "$scene" \
        --source_path "$SOURCE_PATH" \
        --output_path "$OUTPUT_PATH" \
        --no_gpu
    
    if [ $? -eq 0 ]; then
        echo "✓ $scene completed successfully"
    else
        echo "✗ $scene failed"
    fi
    echo
done

echo "================================"
echo "Batch processing complete!"
echo "Results saved to: $OUTPUT_PATH"

