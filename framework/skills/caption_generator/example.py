#!/usr/bin/env python3
"""
Example usage of Caption Generator Skill
"""

import os
import sys

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from skills.caption_generator.agent import CaptionGenerator


def example_bottom_caption():
    """Example: Add caption at bottom"""
    generator = CaptionGenerator()
    
    video_path = "docs/guides/video.mp4"
    
    output = generator.burn_captions(
        video_path=video_path,
        caption_text="Bengaluru, here we come! ☕",
        position="bottom",
        font_size=100,
        font_color="yellow"
    )
    
    print(f"✅ Bottom caption video: {output}")


def example_top_caption():
    """Example: Add caption at top"""
    generator = CaptionGenerator()
    
    video_path = "docs/guides/video.mp4"
    
    output = generator.burn_captions(
        video_path=video_path,
        caption_text="The Jaggery Point",
        position="top",
        font_size=80,
        font_color="white"
    )
    
    print(f"✅ Top caption video: {output}")


def example_custom_style():
    """Example: Custom styling"""
    generator = CaptionGenerator()
    
    video_path = "docs/guides/video.mp4"
    
    output = generator.burn_captions(
        video_path=video_path,
        caption_text="LIMITED TIME OFFER",
        position="center",
        font_size=120,
        font_color="red",
        bg_opacity=0.8,  # More opaque background
        output_path="docs/guides/promo_video.mp4"
    )
    
    print(f"✅ Custom style video: {output}")


if __name__ == "__main__":
    print("📝 Caption Generator Examples\n")
    
    # Run examples
    print("1. Bottom caption (yellow)...")
    example_bottom_caption()
    
    print("\n2. Top caption (white)...")
    example_top_caption()
    
    print("\n3. Custom style (red, center)...")
    example_custom_style()
    
    print("\n✨ All examples completed!")
