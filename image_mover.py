import os
import shutil
import functools
import hashlib
from pathlib import Path
from datetime import datetime
from collections import defaultdict


# ── Configuration ──────────────────────────────────────────────
HOME = Path.home()
DEST = HOME / "Pictures"
EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico", ".icns"}

# State for duplicate checking
_pictures_sizes = defaultdict(list)
_sizes_initialized = False


# ── Helpers ────────────────────────────────────────────────────
def file_digest(path: Path) -> str:
    """Returns the SHA256 hash of a file."""
    h = hashlib.sha256()
    buffer = bytearray(128 * 1024)
    view = memoryview(buffer)
    try:
        with open(path, 'rb', buffering=0) as f:
            for n in iter(lambda: f.readinto(view), 0):
                h.update(view[:n])
    except OSError:
        pass
    return h.hexdigest()

def init_pictures_sizes():
    """Indexes files in the DEST directory by size to quickly find duplicates."""
    global _sizes_initialized
    if _sizes_initialized:
        return
    _sizes_initialized = True
    if DEST.exists():
        for p in DEST.rglob('*'):
            try:
                if p.is_file() and p.suffix.lower() in EXTENSIONS:
                    _pictures_sizes[p.stat().st_size].append(p)
            except OSError:
                pass

def is_duplicate(image: Path) -> bool:
    """Checks if the image already exists in the DEST directory based on size and hash."""
    init_pictures_sizes()
    try:
        size = image.stat().st_size
    except OSError:
        return False
    
    if size not in _pictures_sizes:
        return False
        
    img_hash = None
    for existing_path in _pictures_sizes[size]:
        if img_hash is None:
            img_hash = file_digest(image)
        if file_digest(existing_path) == img_hash:
            return True
    return False

def add_to_index(image_path: Path):
    """Adds a newly copied/moved image to the size index to prevent future duplicates."""
    try:
        _pictures_sizes[image_path.stat().st_size].append(image_path)
    except OSError:
        pass

@functools.lru_cache(maxsize=1024)
def _is_dir_in_git(dir_path: Path) -> bool:
    """Cached helper to check if a directory is within a git repository."""
    try:
        for parent in [dir_path, *dir_path.parents]:
            if (parent / ".git").is_dir():
                return True
            if parent == Path(parent.anchor):
                break
    except Exception:
        pass
    return False

def is_in_git_project(path: Path) -> bool:
    """Traverses up the parent directories to find a .git folder."""
    return _is_dir_in_git(path.parent)

def is_app_image(path: Path) -> bool:
    """
    Detects if an image is likely used by a program (icons, system files).
    Checks against common system/app directories, hidden directories, and filenames.
    """
    system_and_app_dirs = {
        'usr', 'opt', 'var', 'etc', 'snap', 'lib', 'lib64', 'bin', 'sbin', 'boot', 'sys', 'dev', 'run',
        '.local', '.config', '.var', '.cache', '.icons', '.steam', '.nvm', '.npm', 'AppData', 
        'Program Files', 'Program Files (x86)', 'Windows', 'Applications', 'Library'
    }
    
    parts = set(path.parts)
    if parts & system_and_app_dirs:
        return True
    
    # Check if any parent dir is hidden (starts with .)
    for parent in path.parents:
        if parent.name.startswith('.') and parent.name not in {'.', '..'}:
            return True
            
    # Check filename heuristics
    lower_name = path.name.lower()
    if any(keyword in lower_name for keyword in ['icon', 'logo', 'favicon', 'thumb']):
        return True
        
    # Check specific file extensions
    if path.suffix.lower() in {'.ico', '.icns', '.svg'}:
        return True

    return False

def get_dest_folder(path: Path) -> Path:
    """Returns the destination folder based on the file's modification date."""
    try:
        mtime = path.stat().st_mtime
        date = datetime.fromtimestamp(mtime)
        return DEST / f"{date.year}" / f"{date.month:02d}"
    except OSError:
        date = datetime.now()
        return DEST / f"{date.year}" / f"{date.month:02d}"

def find_images(root: Path) -> list[Path]:
    """Finds all images under root, ignoring virtual environments, node_modules, and system mounts."""
    SKIP_DIRS = {
        ".venv", "venv", "env", "node_modules", ".git", "Pictures", "__pycache__",
        "proc", "sys", "dev", "run", "snap", "tmp", "var"
    }
    images = []

    for dirpath, dirnames, filenames in os.walk(root):
        # exclude directories we don't want to traverse
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for filename in filenames:
            try:
                path = Path(dirpath) / filename
                if path.suffix.lower() in EXTENSIONS:
                    if path.is_file():
                        images.append(path)
            except OSError:
                continue

    return images

def process(image: Path, dry_run: bool = False) -> None:
    """Moves or copies the image based on its context (git, app, etc.) and avoids duplicates."""
    try:
        # Skip processing if it's already in the destination folder
        if DEST in image.parents:
            return
    except Exception:
        pass

    if is_duplicate(image):
        action = "skipped (duplicate)"
        prefix = "[DRY RUN] " if dry_run else ""
        try:
            src_str = str(image.relative_to(HOME))
        except ValueError:
            src_str = str(image)
        print(f"{prefix}  {action}  {src_str}")
        return

    dest_folder = get_dest_folder(image)
    if not dry_run:
        try:
            dest_folder.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"  Error creating directory {dest_folder}: {e}")
            return
            
    dest_path = dest_folder / image.name

    # avoid overwriting if a file with the same name exists
    if dest_path.exists():
        stem = image.stem
        suffix = image.suffix
        counter = 1
        while dest_path.exists():
            dest_path = dest_folder / f"{stem}_{counter}{suffix}"
            counter += 1

    in_project = is_in_git_project(image)
    is_app = is_app_image(image)
    
    should_copy = in_project or is_app

    try:
        if should_copy:
            if not dry_run:
                shutil.copy2(image, dest_path)
                add_to_index(dest_path)
            action = "copied"
        else:
            if not dry_run:
                shutil.move(str(image), dest_path)
                add_to_index(dest_path)
            action = "moved "
            
        try:
            src_str = str(image.relative_to(HOME))
        except ValueError:
            src_str = str(image)
        try:
            dst_str = str(dest_path.relative_to(HOME))
        except ValueError:
            dst_str = str(dest_path)
            
        prefix = "[DRY RUN] " if dry_run else ""
        reason = " (app/icon/git)" if should_copy else ""
        print(f"{prefix}  {action}{reason}  {src_str}  →  {dst_str}")
    except Exception as e:
        print(f"  Error processing {image}: {e}")
