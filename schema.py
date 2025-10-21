from pydantic import BaseModel



class StringBase(BaseModel):
    value: str

class StringCreate(StringBase):
    pass


class StringProperties(BaseModel):
    length: int
    is_palindrome: bool
    unique_characters: int
    word_count: int
    sha256_hash: str
    character_frequency_map: dict


class StringResponse(BaseModel):
    id: str
    value: str
    properties: StringProperties
    created_at: str
    class Config:
        orm_mode = True
