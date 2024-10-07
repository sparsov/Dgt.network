from fastapi import APIRouter
from fastapi import Depends, Request
#from app.core.models import User, UserCreate
#from app.core.security import get_password_hash
from app.messaging import getQueryValidator, QueryValidatorHandler
from dgt_sdk.protobuf.validator_pb2 import Message
from dgt_sdk.protobuf import client_peers_pb2

from app.schemas import DgtResponse,DgtMetricResponse,DgtMetricItems
from app.utils.metrics import client
from app.utils.logger import logger as LOGGER 
router = APIRouter()


@router.get("/network/metrics/tps",response_model=DgtMetricResponse)
async def get_metrics_tps(request: Request,trange:str = "24h",tgroup:str = "2m", query: QueryValidatorHandler = Depends(getQueryValidator)):
    # select last(count) from "dgt_validator.executor.TransactionExecutorThread.transaction_execution_count" where time >= now() - 24h and time <= now() group by time(2m),"host" fill(none)
    # SELECT last("count") FROM "dgt_validator.publisher.BlockPublisher.blocks_published_count" WHERE time >= now() - 24h and time <= now() GROUP BY time(2m), "host" fill(none)&epoch=ms
    QUERY_TPS = 'select last(count) from "{}" where time >= now() - {} and time <= now() group by time({}),"host" fill(none)'
    TPS =   "dgt_validator.executor.TransactionExecutorThread.transaction_execution_count"  
    squery  = QUERY_TPS.format(TPS,trange,tgroup) #f'from(bucket: "{BACKET}") |> range(start: -1h) |> filter(fn: (r) => r["_measurement"] == "{TPS}")'   
    #LOGGER.debug("QUERY {}".format(squery))
    results = []
    try:
        if True:
            result = client.query(squery)
            results = list(result.get_points())
        else:
            tables = query_api.query(squery) #, org=org)
            for table in tables:
                for record in table.records:
                    results.append((record.get_field(), record.get_value()))
                    
    except Exception as ex:
        LOGGER.debug("get get data {}".format(ex))

    
    return query._wrap_response(                               
        request,                                              
        data=DgtMetricItems(values=results),                               
        metadata=query._get_metadata(request, None))       
 
@router.get("/network/metrics/latency",response_model=DgtMetricResponse)                                                   
async def get_metrics_latency(request: Request,trange:str = "24h",tgroup:str = "2m",query: QueryValidatorHandler = Depends(getQueryValidator)):             
    LAT ="dgt_validator.interconnect.Interconnect.send_response_time"                                                                                                          
    QUERY_LAT = 'select last(count) from "{}" where time >= now() - {} and time <= now() group by time({}),"host" fill(none)' 
    squery  = QUERY_LAT.format(LAT,trange,tgroup) 
    results = []                                                                                                        
    try:                                                                                                                
        result = client.query(squery)                                                                               
        results = list(result.get_points())                                                                         
    except Exception as ex:                                                                                             
        LOGGER.debug("get get data {}".format(ex))                                                                      
                                                                                                                        
                                                                                                           
    return query._wrap_response(                                                                              
        request,                                                                                              
        data=DgtMetricItems(values=results),                                                                                              
        metadata=query._get_metadata(request, None))   
                                                   



  
@router.get("/network/metrics/entropy",response_model=DgtMetricResponse)                                                                                                                                
async def get_metrics_latency(request: Request,trange:str = "24h",tgroup:str = "2m",query: QueryValidatorHandler = Depends(getQueryValidator)):                                       
                                                                                                                                                 
                                                                                                                                                 
    return query._wrap_response(                                                                                                                 
        request,                                                                                                                                 
        data={},                                                                                                                                 
        metadata=query._get_metadata(request, None))  
                                                                                       
@router.get("/network/metrics/node_activity",response_model=DgtMetricResponse)                                                                                                                                
async def get_metrics_latency(request: Request,trange:str = "24h",tgroup:str = "2m",query: QueryValidatorHandler = Depends(getQueryValidator)):                                       


    return query._wrap_response(                                                                                                                 
        request,                                                                                                                                 
        data={},                                                                                                                                 
        metadata=query._get_metadata(request, None)) 

@router.get("/network/metrics/active_users",response_model=DgtMetricResponse)                                                                                                                                
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

                                                                                       

                                                                                        
                                                                                       
