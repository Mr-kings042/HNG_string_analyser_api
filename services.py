import re
from typing import Any, Dict, List, Optional
from fastapi.encoders import jsonable_encoder
import hashlib
from collections import Counter
from datetime import datetime, timezone
from fastapi import HTTPException
from schema import StringCreate, StringProperties, StringResponse
from sqlalchemy.orm import Session
from logger import get_logger
from models import Strings

logger = get_logger(__name__)


class StringService:
    @staticmethod
    def analyze_string(text: str) -> StringProperties:
        # Normalize for palindrome check
        clean_text = text.strip().lower().replace(" ", "")
        length = len(text)
        is_palindrome = clean_text == clean_text[::-1]
        unique_characters = len(set(text))
        word_count = len(text.split())
        sha256_hash = hashlib.sha256(text.encode()).hexdigest()
        character_frequency_map = dict(Counter(text))

        return StringProperties(
            length=length,
            is_palindrome=is_palindrome,
            unique_characters=unique_characters,
            word_count=word_count,
            sha256_hash=sha256_hash,
            character_frequency_map=character_frequency_map,
        )

    @staticmethod
    def create_string_analysis(db: Session, text: StringCreate) -> StringResponse:
        # Check for missing values
        if not text.value.strip():
            logger.error("String value is required")
            raise HTTPException(status_code=400, detail="String value is required")
        if not isinstance(text.value, str):
            logger.error("String value must be a string")
            raise HTTPException(status_code=400, detail="String value must be a string")
        existing_entry = db.query(Strings).filter(Strings.value == text.value).first()
        if existing_entry:
            raise HTTPException(status_code= 409, detail="String already exists")
        properties = StringService.analyze_string(text.value)

        string_entry = Strings(
            id=str(hashlib.sha256(text.value.encode()).hexdigest()),
            value=text.value,
            properties=jsonable_encoder(properties),
            created_at=datetime.now(timezone.utc),
        )
        db.add(string_entry)
        db.flush()
        db.refresh(string_entry)
        logger.info(f"String analysis created with ID: {string_entry.id}")
        return StringResponse(
            id=string_entry.id,
            value=string_entry.value,
            properties=string_entry.properties,
            created_at=string_entry.created_at.isoformat(),
        )

    @staticmethod
    def get_string_response(db: Session, string_value: str) -> StringResponse:
        string_entry = db.query(Strings).filter(Strings.value == string_value).first()
        if not string_entry:
            raise HTTPException(status_code=404, detail="String not found")
        return StringResponse(
            id=string_entry.id,
            value=string_entry.value,
            properties=string_entry.properties,
            created_at=string_entry.created_at.isoformat(),
        )

    @staticmethod
    async def get_all_strings(db: Session) -> list[StringResponse]:
        string_entries = db.query(Strings).all()
        responses = [
            StringResponse(
                id=entry.id,
                value=entry.value,
                properties=entry.properties,
                created_at=entry.created_at.isoformat(),
            )
            for entry in string_entries
        ]
        return jsonable_encoder(responses)

    @staticmethod
    def filter_strings(
        db: Session,
        is_palindrome: Optional[bool] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        word_count: Optional[int] = None,
        contains_character: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Apply query-parameter filters to filter stored string entries.
         Validates incoming filter values and raises HTTPException(400) for invalid types/values.
         Returns a JSON-serializable list of StringResponse objects (encoded via jsonable_encoder).
        """
        # Validate parameter types/values
        try:
            if is_palindrome is not None and not isinstance(is_palindrome, bool):
                raise HTTPException(
                    status_code=400, detail="is_palindrome must be a boolean"
                )
            if min_length is not None:
                if not isinstance(min_length, int) or min_length < 0:
                    raise HTTPException(
                        status_code=400,
                        detail="min_length must be a non-negative integer",
                    )
            if max_length is not None:
                if not isinstance(max_length, int) or max_length < 0:
                    raise HTTPException(
                        status_code=400,
                        detail="max_length must be a non-negative integer",
                    )
            if (
                min_length is not None
                and max_length is not None
                and min_length > max_length
            ):
                raise HTTPException(
                    status_code=400,
                    detail="min_length cannot be greater than max_length",
                )
            if word_count is not None:
                if not isinstance(word_count, int) or word_count < 0:
                    raise HTTPException(
                        status_code=400,
                        detail="word_count must be a non-negative integer",
                    )
            if contains_character is not None:
                if (
                    not isinstance(contains_character, str)
                    or len(contains_character) != 1
                ):
                    raise HTTPException(
                        status_code=400,
                        detail="contains_character must be a single character string",
                    )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=400, detail="Invalid query parameter values or types"
            )

        entries = db.query(Strings).all()
        filtered_objs: List[StringResponse] = []
        for e in entries:
            props = e.properties or {}
            p_length = props.get("length")
            p_is_pal = props.get("is_palindrome")
            p_word_count = props.get("word_count")

            # apply filters
            if is_palindrome is not None and p_is_pal != is_palindrome:
                continue
            if min_length is not None and (p_length is None or p_length < min_length):
                continue
            if max_length is not None and (p_length is None or p_length > max_length):
                continue
            if word_count is not None and p_word_count != word_count:
                continue
            if contains_character is not None:
                if contains_character not in (e.value or ""):
                    continue

            filtered_objs.append(
                StringResponse(
                    id=e.id,
                    value=e.value,
                    properties=e.properties,
                    created_at=e.created_at.isoformat(),
                )
            )

        data = jsonable_encoder(filtered_objs)
        filters_applied = {
            "is_palindrome": is_palindrome,
            "min_length": min_length,
            "max_length": max_length,
            "word_count": word_count,
            "contains_character": contains_character,
        }

        return {
            "data": data, 
            "count": len(data),
            "filters_applied": filters_applied
            }

    @staticmethod
    def natural_language_query(db: Session, query: str) -> Dict[str, Any]:
        """
        Parse a natural language query string into filter parameters.
        """
        if not query or not query.strip():
            raise HTTPException(status_code=400, detail="Unable to parse natural language query")

        q = query.lower()
        parsed: Dict[str, Any] = {}

        # single word / one word
        if re.search(r"\bsingle[- ]word\b", q) or re.search(r"\bone[- ]word\b", q):
            parsed["word_count"] = 1

        # palindrome
        if "palindr" in q:
            parsed["is_palindrome"] = True

        # longer than N characters -> treat as min_length = N+1
        m = re.search(r"longer than\s+(\d+)", q)
        if m:
            n = int(m.group(1))
            parsed["min_length"] = n + 1

        # containing the letter X (generic)
        m2 = re.search(r"letter\s+([a-z])", q)
        if m2:
            parsed["contains_character"] = m2.group(1)

        # "containing the letter X"
        m3 = re.search(r"containing\s+the\s+letter\s+([a-z])", q)
        if m3:
            parsed["contains_character"] = m3.group(1)

        # "strings containing the letter z" or "containing z"
        m4 = re.search(r"containing\s+([a-z])\b", q)
        if not parsed.get("contains_character") and m4:
            parsed["contains_character"] = m4.group(1)

        # first vowel heuristic
        if "first vowel" in q:
            parsed["contains_character"] = parsed.get("contains_character", "a")

        # Basic conflict detection (if both min and max were parsed somehow)
        if "min_length" in parsed and "max_length" in parsed:
            if parsed["min_length"] > parsed["max_length"]:
                raise HTTPException(status_code=422, detail="Parsed query resulted in conflicting filters")

        if not parsed:
            # could not interpret the query
            raise HTTPException(status_code=400, detail="Unable to parse natural language query")

        # Apply parsed filters using existing filter_strings method
        results = StringService.filter_strings(
            db,
            is_palindrome=parsed.get("is_palindrome"),
            min_length=parsed.get("min_length"),
            max_length=parsed.get("max_length"),
            word_count=parsed.get("word_count"),
            contains_character=parsed.get("contains_character"),
        )

        # results from filter_strings already has shape { data, count, filters_applied }
        return {
            "data": results.get("data"),
            "count": results.get("count"),
            "interpreted_query": {
                "original": query,
                "parsed_filters": parsed,
            },
        }
       

    @staticmethod
    def delete_string(db: Session, string_value: str) -> None:
        string_entry = db.query(Strings).filter(Strings.value == string_value).first()
        if not string_entry:
            raise HTTPException(status_code=404, detail="String not found")
        db.delete(string_entry)
        db.flush()
        logger.info(f"String with value '{string_value}' deleted successfully.")
        return


string_service = StringService()
