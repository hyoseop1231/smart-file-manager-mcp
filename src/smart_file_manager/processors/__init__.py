"""Processors package for Smart File Manager.

This package contains processors for handling different file types
including images and videos.
"""

from smart_file_manager.processors.image_processor import ImageProcessor
from smart_file_manager.processors.video_processor import VideoProcessor

__all__ = ["ImageProcessor", "VideoProcessor"]
