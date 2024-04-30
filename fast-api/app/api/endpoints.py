from fastapi import APIRouter, Depends, Request, HTTPException, status, Security

from app.core.models import User, UserCreate, Token
from app.core.security import get_password_hash, get_username_hash,  verify_password, get_current_user, create_access_token, get_token_sub,oauth2_scheme,ExpiredSignatureError
from fastapi.security import OAuth2PasswordRequestForm
from app.messaging import getQueryValidator, QueryValidatorHandler
from app.db  import TokenDatabase, get_token_db
from app.utils.logger import logger as LOGGER

router = APIRouter()


@router.post("/users", response_model=User)
async def create_user(request: Request,user: UserCreate,token_db: TokenDatabase = Depends(get_token_db)) : #,token: str = Depends(oauth2_scheme)): #User = Depends(get_current_user)):
    # Логика для создания нового пользователя
    # В этом примере мы просто возвращаем переданные данные пользователя
    
    
    username = user.username #get_username_hash(user.username)
    if username in token_db:
        LOGGER.info("already defined user={}".format(username))
        return User(id=1, username=user.username)

    hashed_password = get_password_hash(user.password)
    access_token = create_access_token(data={"sub": user.username})

    created_user = User(username=user.username,password=hashed_password,token=access_token)
    token_db.put(username, created_user.dict())
    LOGGER.info("curr={} token={}".format(username,access_token))

    return created_user

@router.get("/users/me",dependencies=[Depends(oauth2_scheme)])
async def read_current_user(token: str = Security(oauth2_scheme),token_db: TokenDatabase = Depends(get_token_db)):
    try:
        sub = get_token_sub(token)
    except Exception as ex:
        raise HTTPException(status_code=400, detail="Token signature has expired")   
    return token_db.get(sub)

@router.post("/token",response_model=Token)
async def post_token(request: Request,form_data: OAuth2PasswordRequestForm = Depends(),
                     token_db: TokenDatabase = Depends(get_token_db),
                     query: QueryValidatorHandler = Depends(getQueryValidator)
                     ):
    
    username = form_data.username #get_username_hash(form_data.username)
    if username not in token_db:
        raise HTTPException(status_code=400, detail="Incorrect username or password")


    user_dict = token_db.get(username)

    if not verify_password(form_data.password, user_dict["password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = user_dict['token'] #create_access_token(data={"sub": form_data.username })
    try:
        sub = get_token_sub(access_token)
        LOGGER.info('TOKENS SUB={} token={}'.format(sub,access_token))
    except ExpiredSignatureError:
        token_db.put(username, User(username=username,password=user_dict["password"],token=access_token).dict())
        LOGGER.info('GEN NEW TOKENS SUB={} token={}'.format(username,access_token))
    except Exception as ex:
        raise HTTPException(status_code=400, detail="Token signature has expired")

    return Token(access_token=access_token, token_type= "bearer")

@router.get("/token_list")
async def get_token_list(request: Request,token_db: TokenDatabase = Depends(get_token_db),query: QueryValidatorHandler = Depends(getQueryValidator)):
    """
    """
    tlist = []                                                      
    with token_db.cursor() as curs:                                 
        for val in curs.iter():                                     
            LOGGER.info('TOKENS={}'.format(val))                    
            if 'username' in val:                                       
                tlist.append(val)                                   
                                                                    
    
    return query._wrap_response(                               
        request,                                              
        data=tlist,                               
        metadata=query._get_metadata(request, None))                                      
                                                                    


@router.delete("/del_token/{token_id}")
async def del_token(request: Request,token_id: str,token_db: TokenDatabase = Depends(get_token_db),query: QueryValidatorHandler = Depends(getQueryValidator)):
    """
    """
    LOGGER.info('del_token={}...'.format(token_id))               
                                                                   
    if token_id in token_db :                                      
        token =  token_db[token_id]                                
        token_db.delete(token_id)                                  
    else:                                                          
        token = {token_id : 'UNDEFINED'}                           
    
    return query._wrap_response(                               
        request,                                              
        data={"del" : token},                               
        metadata=query._get_metadata(request, None))   
        
        
