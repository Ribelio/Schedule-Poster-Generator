"""
Main entry point for the Schedule Poster Generator.
"""

import argparse
import json
import sys
from pathlib import Path
from renderer import create_poster
from config import PosterConfig, schedule as default_schedule, cover_urls as default_cover_urls, config as default_config

def load_config_from_json(json_path: str):
    """
    Load configuration from a JSON file.
    
    Supports two formats:
    1. GUI preset format (just PosterConfig): { "manga_title": "...", "zoom_factor": ..., ... }
    2. Full format: { "config": {...}, "schedule": [...], "cover_urls": {...} }
    
    Args:
        json_path: Path to JSON configuration file
        
    Returns:
        Tuple of (PosterConfig, schedule, cover_urls)
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Detect format: if it has "config" key, it's the full format
    # Otherwise, if it has PosterConfig fields like "manga_title", it's a GUI preset
    if 'config' in data:
        # Full format: { "config": {...}, "schedule": [...], "cover_urls": {...} }
        poster_config = PosterConfig.from_dict(data['config'])
        schedule = [tuple(item) for item in data['schedule']] if 'schedule' in data else default_schedule
        cover_urls = {int(k): v for k, v in data['cover_urls'].items()} if 'cover_urls' in data else default_cover_urls
    elif 'manga_title' in data or 'zoom_factor' in data:
        # GUI preset format: just PosterConfig fields directly
        poster_config = PosterConfig.from_dict(data)
        schedule = default_schedule
        cover_urls = default_cover_urls
    else:
        # Unknown format, use defaults
        poster_config = default_config
        schedule = default_schedule
        cover_urls = default_cover_urls
    
    return poster_config, schedule, cover_urls

def main():
    parser = argparse.ArgumentParser(
        description='Generate a schedule poster for manga book clubs.'
    )
    parser.add_argument(
        '-c', '--config',
        type=str,
        help='Path to JSON configuration file'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output path for the generated poster'
    )
    
    args = parser.parse_args()
    
    # Load config from JSON if provided, otherwise use defaults
    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"Error: Configuration file not found: {args.config}", file=sys.stderr)
            sys.exit(1)
        
        poster_config, schedule, cover_urls = load_config_from_json(str(config_path))
        
        # Temporarily update the module-level variables for create_poster
        import config as config_module
        original_schedule = config_module.schedule
        original_cover_urls = config_module.cover_urls.copy()
        
        try:
            config_module.schedule = schedule
            config_module.cover_urls.clear()
            config_module.cover_urls.update(cover_urls)
            
            create_poster(poster_config=poster_config, output_path=args.output)
        finally:
            # Restore original values
            config_module.schedule = original_schedule
            config_module.cover_urls.clear()
            config_module.cover_urls.update(original_cover_urls)
    else:
        # Use default config
        create_poster(output_path=args.output)

if __name__ == "__main__":
    main()
