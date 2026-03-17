import sys
from pathlib import Path
from image_mover import HOME, find_images, process


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    if dry_run:
        args.remove("--dry-run")

    if len(args) > 0:
        root = Path(args[0]).expanduser().resolve()
    else:
        root = Path("/")

    if not root.is_dir():
        print(f"Error: {root} is not a directory.")
        return

    print(f"Scanning directory: {root}")
    if dry_run:
        print("Running in DRY RUN mode. No files will be modified.")
        
    images = find_images(root)
    
    if not images:
        print("No images found.")
        return

    print(f"Found {len(images)} images. Processing...")
    for image in images:
        process(image, dry_run=dry_run)

    print(f"\nDone.")


if __name__ == "__main__":
    main()
