from pydantic import BaseModel
from typing import Dict, List, Any, Optional, Union
from dec_dgt.client_cli.dec_attr import DEFAULT_DID

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

class OwnerSignPayload(BaseModel):     

    pubkey     :  str              # owner pub key                              
    signature  :  str              # signature
    payload    :  Optional[bytes] = None            #
                                   
class AccountCreate(BaseModel):
    role        : Optional[str] = "def_role"         
    limit       : Optional[int] = 1001              
    spend_period: Optional[int] = 2                    
    token       : Optional[str] = "DEC"                
    status      : Optional[str] = "on"  
    owner       : OwnerSignPayload


class AssetInfo(BaseModel):
    did    :  Optional[str] = DEFAULT_DID
    name   :  Optional[str] = "Asset name"                           
    url    :  Optional[str] = "url for Asset description"     
    hiden  :  Optional[str] = "hiden description"
    price  :  Optional[int] = 0
    tid    :  Optional[str] = "Asset-ID"
    invoice:  Optional[bool] = False # invoice free 

    
class AssetCreate(BaseModel):
    info    :  Optional[AssetInfo] = None
    signed  :  Optional[OwnerSignPayload] = None 

    
