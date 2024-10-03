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

    emitter    :  str              # owner pub key                              
    signature  :  str              # signature
    payload    :  Optional[bytes] = None            #   
                                   
class AccountInfo(BaseModel):
    role           : Optional[str] = "def_role"         
    limit          : Optional[int] = 1001              
    spend_period   : Optional[int] = 2                    
    token          : Optional[str] = "DEC"                
    status         : Optional[str] = "off" 
    owner_pub_key  : List[str]
    addr_ind       : int = 0   # index into owner_pub_key  for wallet addr 
    sign_min       : int = 1


    

class AccountCreate(BaseModel):  
    info    :  Optional[AccountInfo] = None 
    did     :  str =DEFAULT_DID
    signed  :  Optional[OwnerSignPayload] = None      
    

class AssetInfo(BaseModel):
    
    name           : Optional[str] = "Asset name"                           
    url            : Optional[str] = "url for Asset description"     
    hiden          : Optional[str] = "hiden description"
    price          : Optional[int] = 0
    tips           : Optional[float] = 0.0
    #tid            :  Optional[str] = "Asset-ID"
    invoice        : Optional[bool] = False # invoice free
    owner_pub_key  : List[str] 
    addr_ind       : int = 0   # index into owner_pub_key  for asset addr 
    sign_min       : int = 1                                               
    
class AssetCreate(BaseModel):
    info    :  Optional[AssetInfo] = None
    did     :  str = DEFAULT_DID
    signed  :  Optional[OwnerSignPayload] = None 

class InvoiceInfo(BaseModel):                                                      
    target         : str     # name of target                            
    provement_key  : str     # uniq key for customer                                   
    available_till : Optional[int] = 0                                           
    amount         : float 
    customer       : Optional[str] = None   # fix customer for this invoice
    owner_pub_key  : str                                      

class InvoiceCreate(BaseModel):                          
    info    :  Optional[InvoiceInfo] = None              
    did     :  str = DEFAULT_DID                       
    signed  :  Optional[OwnerSignPayload] = None 
    
class PayInfo(BaseModel):                                                                       
                                                                                            
    #asset          : Optional[str] = None   # asset                                        
    customer       : str                    # key of customer
    owner          : str                    # owner addr 
    did            : Optional[str] = None   # owner did            
    amount         : float                                                      
    tips           : Optional[float] = 0.0                                                  
    tid            : Optional[str] = None # tid for multi signed                                           
    provement_key  : Optional[str] = None # Provement key refer to prov key from invoice
    passkey        : Optional[str] = None # passkey for special operation  
                                          # 
class PayTrans(BaseModel):                          
    info    :  Optional[PayInfo] = None              
    did     :  str = DEFAULT_DID        # customer did                     
    signed  :  Optional[OwnerSignPayload] = None                                                         
    

class CertInfo(BaseModel):
    COUNTRY_NAME              : str = "CA"
    STATE_OR_PROVINCE_NAME    : str = "ONTARIO"
    LOCALITY_NAME             : str = "BARRIE"
    ORGANIZATION_NAME         : str = "YOUR ORGANIZATION NAME" 
    COMMON_NAME               : str = "NODE SAMPLE"
    DNS_NAME                  : str = "dgt.world"
    EMAIL_ADDRESS             : str = "adminmail@mail.com"
    PSEUDONYM                 : str = "dgt00000000000000000"
    JURISDICTION_COUNTRY_NAME : str = "CA"
    BUSINESS_CATEGORY         : str = "YOUR BUSINESS CATEGORY"
    USER_ID                   : str = "000000000000000001" 
    #
    FIRST_NAME                : Optional[str] = "CA"
    LAST_NAME                 : Optional[str] = "CA"
    PHONE                     : Optional[str] = "CA"
    FULL_ADDRESS              : Optional[str] = "CA"
    DATE_OF_BIRTH             : Optional[str] = "CA"
    PASSPORT_ID_DOCUMENT      : Optional[str] = "CA" # hash
    PHOTOGRAPH                : Optional[str] = "CA" # hash

class CertInfoCreate(BaseModel):                            
    cert         : CertInfo                
    owner        : str 

        
class CertCreate(BaseModel):                                   
    info         : CertInfoCreate                
    signed       : Optional[OwnerSignPayload] = None
    photograph   : Optional[bytes] = None           
    document     : Optional[bytes] = None 
