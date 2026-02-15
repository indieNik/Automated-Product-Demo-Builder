#!/usr/bin/env python3
"""
Workspace Cleanup Script

Resets the INPUT and OUTPUT directories to a clean state for a fresh pipeline run.
Deletes generated configs, recordings, scripts, and media files.
"""

import shutil
import os
from pathlib import Path

def clean_workspace():
    # Define roots
    framework_dir = Path(__file__).parent.resolve()
    project_root = framework_dir.parent
    
    input_dir = project_root / "INPUT"
    output_dir = project_root / "OUTPUT"
    
    # Files/Dirs to clear (content only or recreate)
    # We remove the folders and recreate them to ensure they are empty
    paths_to_clean = [
        input_dir / "configuration" / "Product_Specs.json",
        input_dir / "raw_recordings",
        output_dir / "scripts",
        output_dir / "scenes",
        output_dir / "voiceover",
        output_dir / "captions",
        output_dir / "final_video",
        output_dir / "temp"
    ]
    
    print(f"🧹 Cleaning workspace at {project_root}...")
    
    for path in paths_to_clean:
        if path.exists():
            if path.is_file():
                try:
                    path.unlink()
                    print(f"   Deleted file: {path.relative_to(project_root)}")
                except Exception as e:
                    print(f"   ❌ Failed to delete {path.name}: {e}")
            elif path.is_dir():
                try:
                    shutil.rmtree(path)
                    print(f"   Deleted dir:  {path.relative_to(project_root)}")
                except Exception as e:
                    print(f"   ❌ Failed to delete {path.name}: {e}")
        else:
            print(f"   (Skipped, not found: {path.name})")

    # Recreate necessary directory structure
    print("\n🏗️  Recreating directory structure...")
    
    dirs_to_create = [
        input_dir / "configuration",
        input_dir / "raw_recordings",
        output_dir / "scripts",
        output_dir / "scenes",
        output_dir / "voiceover",
        output_dir / "captions",
        output_dir / "final_video"
    ]
    
    for d in dirs_to_create:
        d.mkdir(parents=True, exist_ok=True)
        print(f"   Created: {d.relative_to(project_root)}/")
        
    print("\n✅ Workspace reset complete. Ready for new run.")

if __name__ == "__main__":
    clean_workspace()
