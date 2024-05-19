from pydantic import BaseModel
from typing import Dict, List, Any, Optional

class DgtBaseResponse(BaseModel):
    link: str


class DgtResponse(DgtBaseResponse):
    data: Dict[str,Any]

class DgtListResponse(DgtBaseResponse):
    data: List[Any]

class DgtPagingListResponse(DgtListResponse):
    head: Optional[str]
    paging: Dict[str,Any]

class DgtPagingDictResponse(DgtResponse):
    head: Optional[str]
    paging: Dict[str,Any]


class UserBase(BaseModel):
    name: str


class UserCreate(UserBase):
    password: str
    email   : str

class UserOut(UserBase):
    id: int

    class Config:
        from_attributes = True
        #orm_mode = True

class AccountCreate(BaseModel):
    role        : Optional[str] = "def_role"         
    limit       : Optional[int] = 1001              
    spend_period: Optional[int] = 2                    
    token       : Optional[str] = "DEC"                
    status      : Optional[str] = "on"  
    
class AssetCreate(BaseModel):
    name   :  Optional[str] = "target"                           
    url    :  Optional[str] = "url for target description"     
    hiden  :  Optional[str] = "hiden description"
    price  :  Optional[int] = 1
    tid    :  Optional[str] = "Target-ID"             
