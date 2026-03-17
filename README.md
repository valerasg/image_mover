# image-mover

`image-mover` is a smart Python utility that helps you organize images scattered across your system by moving or copying them to your `~/Pictures` directory, neatly organized by date.

## Features

- **Smart Organization:** Automatically organizes images into `~/Pictures/YYYY/MM` folders based on their modification date.
- **Intelligent Copy vs. Move:**
  - Safely **copies** images if they belong to a git repository, system directories, or look like application assets (e.g., icons, SVGs).
  - **Moves** standard images to clean up your directories.
- **Deduplication:** Prevents duplicate files by checking file sizes and SHA256 hashes before copying/moving.
- **Dry Run Support:** Test what the script will do without actually moving or modifying any files.
- **Dependency-Free:** Built entirely with the Python standard library.

## Requirements

- Python >= 3.14

## Usage

You can run the script via `uv` or directly with Python:

```bash
python main.py
```

### Configuration
The script automatically ignores common non-user directories such as `.venv`, `node_modules`, `.git`, and system mount points to ensure it only processes relevant files.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
