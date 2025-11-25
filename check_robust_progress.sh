#!/bin/bash
# Check progress of robust COLMAP batch processing

ROBUST_DIR="/home/runw/Project/LSM/data/scannet_test_colmap_robust"
LOG_FILE="/home/runw/Project/LSM/colmap_robust_batch.log"

echo "========================================="
echo "ROBUST COLMAP Progress Check"
echo "========================================="
echo "Time: $(date)"
echo ""

# Count completed scenes
if [ -d "$ROBUST_DIR" ]; then
    total_scenes=$(ls -d "$ROBUST_DIR"/scene* 2>/dev/null | wc -l)
    successful=0
    failed=0
    
    for scene_dir in "$ROBUST_DIR"/scene*; do
        scene=$(basename "$scene_dir")
        
        if [ -f "$scene_dir/sparse/0/images.bin" ]; then
            successful=$((successful + 1))
        else
            failed=$((failed + 1))
        fi
    done
    
    echo "Processed: $total_scenes / 40 scenes"
    echo "  ✅ Successful: $successful"
    echo "  ❌ Failed: $failed"
else
    echo "No output directory yet. Processing may be starting..."
fi

echo ""
echo "========================================="
echo "Recent log activity (last 20 lines):"
echo "========================================="
if [ -f "$LOG_FILE" ]; then
    tail -20 "$LOG_FILE"
else
    echo "Log file not found. Processing may not have started yet."
fi

echo ""
echo "To monitor live: tail -f $LOG_FILE"

