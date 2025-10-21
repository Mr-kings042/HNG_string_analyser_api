from fastapi import APIRouter, Response,status, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services import string_service
from schema import StringCreate, StringResponse
from logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post("", response_model=StringResponse, status_code=status.HTTP_201_CREATED)
def create_string(string: StringCreate, db: Session = Depends(get_db)):
   """Create a new string analysis entry."""
   try:
        logger.info(f"Creating string with value: {string.value}")
        string_response = string_service.create_string_analysis(db, string)
        db.commit()
        return string_response
   except HTTPException as se:
        logger.error(f"Error creating string: {se.detail}")
        db.rollback()
        raise se
   except Exception as e:
        logger.error(f"Error creating string: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

@router.get("/{string_value}", response_model=StringResponse, status_code=status.HTTP_200_OK)
def read_string(string_value: str, db: Session = Depends(get_db)):
    """Retrieve a string analysis entry by its value."""
    try:
        logger.info(f"Fetching string with value: {string_value}")
        string_response = string_service.get_string_response(db, string_value)
        return string_response
    except HTTPException as he:
        logger.error(f"Error fetching string: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"Error fetching string: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@router.get("", status_code=status.HTTP_200_OK)
def filter_strings(
    is_palindrome: bool | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    word_count: int | None = None,
    contains_character: str | None = None,
    db: Session = Depends(get_db)
):
    """Filter string analysis entries based on criteria."""
    try:
        logger.info(
            f"Filtering strings with min_length={min_length}, "
            f"max_length={max_length}, contains='{contains_character}'"
        )
        filtered_strings = string_service.filter_strings(
            db, is_palindrome, min_length, max_length, word_count, contains_character
        )
        return filtered_strings
    except HTTPException as e:
        logger.error(f"Error filtering strings: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error filtering strings: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
@router.get("/filter-by-natural-language", status_code=status.HTTP_200_OK)
def filter_by_natural_language(query: str, db: Session = Depends(get_db)):
    """Filter strings based on a natural language query."""
    try:
        logger.info(f"Filtering strings with natural language query: {query}")
        # natural_language_query now parses + applies filters and returns the full response
        response = string_service.natural_language_query(db, query)
        return response
    except HTTPException as ce:
        logger.error(f"Error filtering strings: {ce.detail}")
        raise ce
    except Exception as e:
        logger.error(f"Error filtering strings: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")



# @router.get("/strings/all", response_model=list[StringResponse], status_code=status.HTTP_200_OK)
# async def get_all_strings(db: Session = Depends(get_db)):
#     """Retrieve all string."""
#     logger.info("Fetching all strings")
#     return await string_service.get_all_strings(db)


@router.delete("/{string_value}", status_code=status.HTTP_204_NO_CONTENT)
def delete_string(string_value: str, db: Session = Depends(get_db)):
    """Delete a string analysis entry by its value."""
    try:
        logger.info(f"Deleting string with value: {string_value}")
        string_service.delete_string(db, string_value)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException as he:
        logger.error(f"Error deleting string: {str(he.detail)}")
        db.rollback()
        raise he
    except Exception as e:
        logger.error(f"Error deleting string: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")