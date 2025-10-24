from pydantic import BaseModel, EmailStr
from datetime import datetime

# Defines the common fields for a post
class PostBase(BaseModel):
    title: str
    content: str
    published: bool = True

# Defines the fields required to CREATE a post.
# It inherits everything from PostBase.
class PostCreate(PostBase):
    pass

# Defines the shape of the data to be RETURNED to the user.
# It inherits from PostBase and adds database-generated fields.
class Post(PostBase):
    id: int
    

    class Config:
        from_attributes = True
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    
class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime
    class Config:
        # For Pydantic v2 (recommended)
        from_attributes = True