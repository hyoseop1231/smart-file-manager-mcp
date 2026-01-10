"""Constants for Smart File Manager.

TAG: VIS-M1-02, STT-001
SPEC: SPEC-VISION-001, SPEC-STT-001

This module defines all constants used by the Vision analysis and STT services,
including supported formats, size limits, cache settings, and prompts.
"""

# =============================================================================
# Supported File Formats
# =============================================================================

SUPPORTED_IMAGE_FORMATS: frozenset[str] = frozenset(
    {
        "jpeg",
        "jpg",
        "png",
        "gif",
        "webp",
        "bmp",
    }
)

SUPPORTED_VIDEO_FORMATS: frozenset[str] = frozenset(
    {
        "mp4",
        "mkv",
        "avi",
        "mov",
        "webm",
    }
)

# =============================================================================
# MIME Type Mappings
# =============================================================================

IMAGE_MIME_TYPES: dict[str, str] = {
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
    "bmp": "image/bmp",
}

VIDEO_MIME_TYPES: dict[str, str] = {
    "mp4": "video/mp4",
    "mkv": "video/x-matroska",
    "avi": "video/x-msvideo",
    "mov": "video/quicktime",
    "webm": "video/webm",
}

# =============================================================================
# Size Limits
# =============================================================================

# Image size limits
MAX_IMAGE_SIZE_BYTES: int = 20 * 1024 * 1024  # 20MB
MAX_IMAGE_DIMENSION: int = 8192  # 8192px max width/height
TARGET_IMAGE_DIMENSION: int = 4096  # 4096px target for resizing

# Video size limits
MAX_VIDEO_SIZE_BYTES: int = 500 * 1024 * 1024  # 500MB
MAX_VIDEO_DURATION_SECONDS: int = 30 * 60  # 30 minutes

# =============================================================================
# Cache Settings
# =============================================================================

VISION_CACHE_TTL_SECONDS: int = 7 * 24 * 60 * 60  # 7 days

# Cache key prefixes
VISION_CACHE_KEY_PREFIX_IMAGE: str = "vision:image:"
VISION_CACHE_KEY_PREFIX_VIDEO: str = "vision:video:"
VISION_CACHE_KEY_PREFIX_FRAME: str = "vision:frame:"

# =============================================================================
# Video Keyframe Extraction Settings
# =============================================================================

# Keyframe intervals based on video duration
# Format: {max_duration_seconds: (interval_seconds, max_frames)}
KEYFRAME_INTERVALS: dict[int, tuple[int, int]] = {
    60: (5, 12),  # 0-60 seconds: 5s interval, max 12 frames
    300: (15, 20),  # 1-5 minutes: 15s interval, max 20 frames
    600: (30, 20),  # 5-10 minutes: 30s interval, max 20 frames
    1800: (60, 30),  # 10-30 minutes: 60s interval, max 30 frames
}

# Maximum representative frames for API analysis
MAX_REPRESENTATIVE_FRAMES: int = 5

# =============================================================================
# Analysis Prompt Templates
# =============================================================================

IMAGE_ANALYSIS_PROMPT: str = """Analyze this image and provide a structured JSON response with:
1. description: A detailed description of the image content (2-3 sentences)
2. objects: List of detected objects with confidence scores (0.0-1.0)
3. scene: The overall scene type (indoor, outdoor, nature, urban, etc.)
4. text: Any visible text in the image (OCR)
5. tags: List of relevant tags for searchability
6. dominant_colors: Top 3 dominant colors in the image
7. quality: Image quality assessment (sharp, blurry, dark, overexposed, etc.)

Respond ONLY with valid JSON, no additional text. Use this exact structure:
{
  "description": "string",
  "objects": [{"name": "string", "confidence": 0.0}],
  "scene": "string",
  "text": "string or null",
  "tags": ["string"],
  "dominant_colors": ["string"],
  "quality": "string"
}"""

# =============================================================================
# Vision Model Configuration
# =============================================================================

# Primary model for vision analysis (Balanced)
VISION_PRIMARY_MODEL: str = "google/gemini-2.0-flash-001"

# Fallback 1 model (Low-cost, Korean optimized)
VISION_FALLBACK_1_MODEL: str = "qwen/qwen2.5-vl-32b-instruct"

# Fallback 2 model (Free tier)
VISION_FALLBACK_2_MODEL: str = "google/gemini-2.0-flash-exp:free"

# Model timeouts (seconds)
VISION_PRIMARY_TIMEOUT: float = 30.0
VISION_FALLBACK_1_TIMEOUT: float = 30.0
VISION_FALLBACK_2_TIMEOUT: float = 60.0  # Free tier may be slower

# =============================================================================
# Budget Settings
# =============================================================================

VISION_DAILY_BUDGET_USD: float = 1.00
VISION_MONTHLY_BUDGET_USD: float = 30.00

# =============================================================================
# STT (Speech-to-Text) Constants (TAG: STT-001, SPEC-STT-001)
# =============================================================================

# Supported audio formats for STT processing (REQ-U-001)
SUPPORTED_AUDIO_FORMATS: frozenset[str] = frozenset(
    {
        "mp3",
        "wav",
        "flac",
        "aac",
        "ogg",
        "m4a",
        "opus",
        "wma",
    }
)

# Audio MIME type mappings
AUDIO_MIME_TYPES: dict[str, str] = {
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "flac": "audio/flac",
    "aac": "audio/aac",
    "ogg": "audio/ogg",
    "m4a": "audio/mp4",
    "opus": "audio/opus",
    "wma": "audio/x-ms-wma",
}

# STT Cache settings
STT_CACHE_PREFIX: str = "stt"
STT_CACHE_TTL_SECONDS: int = 7 * 24 * 60 * 60  # 7 days

# STT Size and Duration limits (REQ-N-001, REQ-N-002)
STT_MAX_DURATION_SECONDS: int = 2 * 60 * 60  # 2 hours (7200 seconds)
STT_MAX_FILE_SIZE_BYTES: int = 100 * 1024 * 1024  # 100MB

# STT Model configuration
STT_DEFAULT_MODEL_SIZE: str = "large-v3"
STT_DEFAULT_DEVICE: str = "auto"
STT_DEFAULT_COMPUTE_TYPE: str = "auto"
STT_DEFAULT_BATCH_SIZE: int = 16
STT_CHUNK_LENGTH_SECONDS: int = 30
