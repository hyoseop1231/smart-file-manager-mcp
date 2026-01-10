"""Tag generator for file classification.

TAG: CLASS-001-M2
SPEC: SPEC-CLASS-001

This module provides the TagGenerator class for generating
tags from VisionService results and file metadata.
"""


from smart_file_manager.classification.models import (
    Classification,
    FileMetadata,
    TagSet,
)
from smart_file_manager.services.vision_models import (
    ImageAnalysisResult,
    VideoAnalysisResult,
)

# Default translation dictionary for common tags
DEFAULT_TRANSLATION_DICT: dict[str, str] = {
    # Objects
    "person": "사람",
    "people": "사람들",
    "man": "남자",
    "woman": "여자",
    "child": "어린이",
    "baby": "아기",
    "dog": "개",
    "cat": "고양이",
    "bird": "새",
    "car": "자동차",
    "truck": "트럭",
    "bus": "버스",
    "bicycle": "자전거",
    "motorcycle": "오토바이",
    "airplane": "비행기",
    "boat": "보트",
    "train": "기차",
    "building": "건물",
    "house": "집",
    "tree": "나무",
    "flower": "꽃",
    "plant": "식물",
    "food": "음식",
    "fruit": "과일",
    "vegetable": "채소",
    "book": "책",
    "phone": "전화기",
    "computer": "컴퓨터",
    "laptop": "노트북",
    "table": "테이블",
    "chair": "의자",
    "bed": "침대",
    "door": "문",
    "window": "창문",
    "sky": "하늘",
    "cloud": "구름",
    "sun": "태양",
    "moon": "달",
    "star": "별",
    "water": "물",
    "ocean": "바다",
    "sea": "바다",
    "river": "강",
    "lake": "호수",
    "mountain": "산",
    "hill": "언덕",
    "grass": "잔디",
    "road": "도로",
    "street": "거리",
    "bridge": "다리",
    # Scenes
    "outdoor": "야외",
    "indoor": "실내",
    "nature": "자연",
    "urban": "도시",
    "rural": "시골",
    "city": "도시",
    "beach": "해변",
    "forest": "숲",
    "park": "공원",
    "garden": "정원",
    "office": "사무실",
    "home": "집",
    "restaurant": "식당",
    "shop": "가게",
    "store": "상점",
    "mall": "쇼핑몰",
    "school": "학교",
    "hospital": "병원",
    "airport": "공항",
    "station": "역",
    "studio": "스튜디오",
    "gym": "체육관",
    "stadium": "경기장",
    "museum": "박물관",
    "library": "도서관",
    "church": "교회",
    "temple": "사원",
    # Categories
    "photo": "사진",
    "screenshot": "스크린샷",
    "document": "문서",
    "artwork": "아트워크",
    "meme": "밈",
    "product": "제품",
    "video": "비디오",
    "other": "기타",
    # Sub-categories
    "portrait": "인물",
    "landscape": "풍경",
    "macro": "접사",
    "aerial": "항공",
    "desktop": "데스크톱",
    "mobile": "모바일",
    "web": "웹",
    "game": "게임",
    "scan": "스캔",
    "receipt": "영수증",
    "id_card": "신분증",
    "form": "양식",
    "illustration": "일러스트",
    "painting": "그림",
    "digital_art": "디지털아트",
    "reaction": "리액션",
    "text_meme": "텍스트밈",
    "comic": "만화",
    "electronics": "전자제품",
    "fashion": "패션",
    "clip": "클립",
    "movie": "영화",
    "recording": "녹화",
    "tutorial": "튜토리얼",
    # Quality
    "sharp": "선명한",
    "blurry": "흐릿한",
    "dark": "어두운",
    "bright": "밝은",
    "overexposed": "과다노출",
    # Time
    "morning": "아침",
    "afternoon": "오후",
    "evening": "저녁",
    "night": "밤",
    "day": "낮",
    "sunrise": "일출",
    "sunset": "일몰",
    # Months
    "january": "1월",
    "february": "2월",
    "march": "3월",
    "april": "4월",
    "may": "5월",
    "june": "6월",
    "july": "7월",
    "august": "8월",
    "september": "9월",
    "october": "10월",
    "november": "11월",
    "december": "12월",
    # Colors
    "red": "빨강",
    "blue": "파랑",
    "green": "초록",
    "yellow": "노랑",
    "orange": "주황",
    "purple": "보라",
    "pink": "분홍",
    "brown": "갈색",
    "black": "검정",
    "white": "흰색",
    "gray": "회색",
    "grey": "회색",
    # Other common
    "pet": "애완동물",
    "animal": "동물",
    "traffic": "교통",
    "screen": "화면",
    "text": "텍스트",
}

# Month number to name mapping
MONTH_NAMES: dict[int, str] = {
    1: "january",
    2: "february",
    3: "march",
    4: "april",
    5: "may",
    6: "june",
    7: "july",
    8: "august",
    9: "september",
    10: "october",
    11: "november",
    12: "december",
}


class TagGenerator:
    """Generator for file classification tags.

    This class generates tags from VisionService analysis results
    and file metadata, with support for English-Korean translation.

    Attributes:
        max_tags: Maximum number of tags to generate.
        _translation_dict: Dictionary mapping English tags to Korean.
    """

    def __init__(
        self,
        max_tags: int = 20,
        translation_dict: dict[str, str] | None = None,
    ) -> None:
        """Initialize the TagGenerator.

        Args:
            max_tags: Maximum number of tags to generate (default 20).
            translation_dict: Optional custom translation dictionary.
        """
        self.max_tags = max_tags
        self._translation_dict = translation_dict or DEFAULT_TRANSLATION_DICT

    def generate_tags(
        self,
        vision_result: ImageAnalysisResult | VideoAnalysisResult | None,
        metadata: FileMetadata,
        classification: Classification,
        *,
        max_tags: int | None = None,
    ) -> TagSet:
        """Generate tags for a file.

        Args:
            vision_result: Optional VisionService analysis result.
            metadata: File metadata.
            classification: Classification result.
            max_tags: Override for maximum tags (uses instance max_tags if None).

        Returns:
            TagSet with English and Korean tags.
        """
        effective_max_tags = max_tags if max_tags is not None else self.max_tags

        # Collect tags from various sources
        tags_by_source: dict[str, list[str]] = {
            "objects": [],
            "scene": [],
            "vision_tags": [],
            "metadata": [],
            "category": [],
        }

        # Extract tags from vision result
        if vision_result is not None:
            # Objects
            if hasattr(vision_result, "objects"):
                for obj in vision_result.objects:
                    tags_by_source["objects"].append(obj.name.lower())

            # Scene
            if hasattr(vision_result, "scene") and vision_result.scene:
                tags_by_source["scene"].append(vision_result.scene.lower())

            # Vision tags
            if hasattr(vision_result, "tags"):
                for tag in vision_result.tags:
                    tags_by_source["vision_tags"].append(tag.lower())

        # Extract tags from metadata
        if metadata.extension:
            tags_by_source["metadata"].append(metadata.extension.lower())

        # Extract date tags from EXIF
        if metadata.exif and "DateTimeOriginal" in metadata.exif:
            date_tags = self._extract_date_tags(metadata.exif["DateTimeOriginal"])
            tags_by_source["metadata"].extend(date_tags)

        # Add category tags
        tags_by_source["category"].append(classification.category.lower())
        if classification.sub_category:
            tags_by_source["category"].append(classification.sub_category.lower())

        # Deduplicate and combine all tags
        seen_lower: set[str] = set()
        all_tags: list[str] = []

        # Process sources in priority order
        for source in ["objects", "scene", "vision_tags", "category", "metadata"]:
            for tag in tags_by_source[source]:
                tag_lower = tag.lower()
                if tag_lower not in seen_lower:
                    seen_lower.add(tag_lower)
                    all_tags.append(tag_lower)

        # Limit to max tags
        all_tags = all_tags[:effective_max_tags]

        # Build source breakdown (after deduplication)
        source_breakdown: dict[str, list[str]] = {}
        for source, tags in tags_by_source.items():
            unique_tags = []
            seen_in_source: set[str] = set()
            for tag in tags:
                tag_lower = tag.lower()
                if tag_lower not in seen_in_source and tag_lower in seen_lower:
                    seen_in_source.add(tag_lower)
                    if tag_lower in all_tags:
                        unique_tags.append(tag_lower)
            if unique_tags:
                source_breakdown[source] = unique_tags

        # Translate to Korean
        tags_ko = self.translate_tags(all_tags)

        return TagSet(
            tags_en=all_tags,
            tags_ko=tags_ko,
            source_breakdown=source_breakdown,
        )

    def translate_tags(
        self,
        tags: list[str],
        target_language: str = "ko",
    ) -> list[str]:
        """Translate tags to target language.

        Args:
            tags: List of English tags.
            target_language: Target language code (default "ko" for Korean).

        Returns:
            List of translated tags.
        """
        if target_language != "ko":
            # Only Korean translation is currently supported
            return tags

        translated = []
        for tag in tags:
            tag_lower = tag.lower()
            if tag_lower in self._translation_dict:
                translated.append(self._translation_dict[tag_lower])
            else:
                # Return original if no translation found
                translated.append(tag)

        return translated

    def _extract_date_tags(self, datetime_str: str) -> list[str]:
        """Extract date-based tags from EXIF datetime string.

        Args:
            datetime_str: EXIF datetime string (e.g., "2026:01:10 10:00:00").

        Returns:
            List of date-based tags.
        """
        tags = []

        try:
            # Parse EXIF format: "YYYY:MM:DD HH:MM:SS"
            date_part = datetime_str.split(" ")[0]
            parts = date_part.split(":")

            if len(parts) >= 2:
                year = parts[0]
                month = int(parts[1])

                # Add year as tag
                tags.append(year)

                # Add month name
                if month in MONTH_NAMES:
                    tags.append(MONTH_NAMES[month])

        except (ValueError, IndexError):
            # If parsing fails, return empty list
            pass

        return tags
