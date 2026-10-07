#!/bin/bash

ROOT="${1:-archive/CIFAR-10-images-master}"

for split in train test; do
  [ "$split" = "train" ] && expected=5000 || expected=1000
  echo "== $split (expected $expected per class) =="
  total=0
  for dir in "$ROOT/$split"/*/; do
    [ -d "$dir" ] || continue
    n=$(find "$dir" -maxdepth 1 -type f | wc -l)
    total=$((total + n))
    status="OK"
    [ "$n" -ne "$expected" ] && status="MISMATCH"
    printf "%-12s %6d  %s\n" "$(basename "$dir")" "$n" "$status"
  done
  echo "Total: $total"
  echo
done