#!/bin/bash
# List of directories to create
directories=(
    "BlackbeardCove"
    "TreasureIsland"
    "SkullAndBonesReef"
    "DeadMansBay"
    "JollyRogersHarbor"
    "BuccaneerBeach"
    "PirateHideout"
    "CutthroatCreek"
    "SirenShores"
    "CorsairCastle"
    "WickedWaters"
    "MaroonersLagoon"
    "ParrotPerch"
    "RumRunnersRidge"
    "GalleonGraveyard"
)
# Create directories if they don't exist and change their ownership to service:service
for dir in "${directories[@]}"; do
    full_path="/data/$dir"
    if [ ! -d "$full_path" ]; then
        mkdir -p "$full_path"
        echo "Created directory: $full_path"
    else
        echo "Directory already exists: $full_path"
    fi
    # Change ownership to service:service
    chown service:service "$full_path"
done