from fastapi import APIRouter
from fastapi import Depends, Request
#from app.core.models import User, UserCreate
#from app.core.security import get_password_hash
from app.messaging import getQueryValidator, QueryValidatorHandler
from dgt_sdk.protobuf.validator_pb2 import Message
from dgt_sdk.protobuf import client_peers_pb2

from app.schemas import DgtResponse
from app.utils.metrics import query_api
from app.utils.logger import logger as LOGGER 
router = APIRouter()
QUERY = '''
from(bucket: "your_bucket")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "dgt_validator.executor.TransactionExecutorThread.transaction_execution_count")
'''

@router.get("/network/metrics/tps",response_model=DgtResponse)
async def get_metrics_tps(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):
    TPS =   "dgt_validator.executor.TransactionExecutorThread.transaction_execution_count"  
    BACKET = "B1"
    squery  = QUERY #f'from(bucket: "{BACKET}") |> range(start: -1h) |> filter(fn: (r) => r["_measurement"] == "{TPS}")'   
    LOGGER.debug("QUERY {}".format(QUERY))
    results = []
    try:
        tables = query_api.query(squery) #, org=org)
        for table in tables:
            for record in table.records:
                results.append((record.get_field(), record.get_value()))
    except Exception as ex:
        LOGGER.debug("get get data {}".format(ex))

    
    return query._wrap_response(                               
        request,                                              
        data={"data" :results},                               
        metadata=query._get_metadata(request, None))       
 
@router.get("/network/metrics/latency",response_model=DgtResponse)                                                   
async def get_metrics_latency(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):             
                                                                                                              
                                                                                                              
    return query._wrap_response(                                                                              
        request,                                                                                              
        data={},                                                                                              
        metadata=query._get_metadata(request, None))   
                                                   



  
@router.get("/network/metrics/entropy",response_model=DgtResponse)                                                                                                                                
async def get_metrics_latency(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):                                       
                                                                                                                                                 
                                                                                                                                                 
    return query._wrap_response(                                                                                                                 
        request,                                                                                                                                 
        data={},                                                                                                                                 
        metadata=query._get_metadata(request, None))  
                                                                                       
@router.get("/network/metrics/node_activity",response_model=DgtResponse)                                                                                                                                
async def get_metrics_latency(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):                                       


    return query._wrap_response(                                                                                                                 
        request,                                                                                                                                 
        data={},                                                                                                                                 
        metadata=query._get_metadata(request, None)) 

@router.get("/network/metrics/active_users",response_model=DgtResponse)                                                                                                                                
async def get_metrics_latency(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):                                       


    return query._wrap_response(                                                                                                                 
        request,                                                                                                                                 
        data={},                                                                                                                                 
        metadata=query._get_metadata(request, None))  
                                                                                       
@router.get("/network/metrics/blockchain_size",response_model=DgtResponse)                                                                                                                                
async def get_metrics_latency(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):                                       


    return query._wrap_response(                                                                                                                 
        request,                                                                                                                                 
        data={},                                                                                                                                 
        metadata=query._get_metadata(request, None))                                                                                         

                                                                                       

                                                                                        
                                                                                       
