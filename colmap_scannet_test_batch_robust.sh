#!/bin/bash
# Batch script to run ROBUST COLMAP on ALL ScanNet test scenes

SOURCE_PATH="/home/runw/Project/data/colmap/data/scannet_test_preprocessed"
OUTPUT_PATH="/home/runw/Project/LSM/data/scannet_test_colmap_robust"

# Get list of ALL scenes from source directory
scenes=$(ls "$SOURCE_PATH" | grep "^scene")

total=$(echo "$scenes" | wc -l)
current=0

echo "Found $total scenes to process with ROBUST COLMAP settings"
echo "================================================================"
echo

success_count=0
fail_count=0

for scene in $scenes; do
    current=$((current + 1))
    echo "[$current/$total] Processing $scene with ROBUST mode..."
    
    python /home/runw/Project/LSM/colmap_scannet_test_robust.py \
        --scene "$scene" \
        --source_path "$SOURCE_PATH" \
        --output_path "$OUTPUT_PATH" \
        --no_gpu
    
    if [ $? -eq 0 ]; then
        echo "✓ $scene completed successfully"
        success_count=$((success_count + 1))
    else
        echo "✗ $scene failed (continuing with next...)"
        fail_count=$((fail_count + 1))
    fi
    echo
done

echo "================================================================"
echo "Processing Summary:"
echo "  ✅ Successful: $success_count / $total"
echo "  ❌ Failed: $fail_count / $total"
echo "================================================================"

echo "================================================================"
echo "Batch ROBUST COLMAP processing complete!"
echo "Results saved to: $OUTPUT_PATH"
echo
echo "Next steps:"
echo "1. Check results to see which scenes improved"
echo "2. Run combine script to merge with original results"
echo "3. Process the best combined scenes with 3DGS training"

