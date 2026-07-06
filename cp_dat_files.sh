find . -name "*.dat" -type f | while read -r file; do
    # Get the parent folder name
    parent=$(basename "$(dirname "$file")")
    # Get the actual filename
    filename=$(basename "$file")
    # Copy and rename: e.g., /dest/folder1_report.pdf
    cp "$file" "../chapel-riscv/p550/${parent}_${filename}"
done
