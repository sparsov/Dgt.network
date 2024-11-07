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
QUERY_FMT = 'select last(count) from "{}" where time >= {} and time <= {} group by time({}),"host" fill(none)'

def get_time_range(from_tm,to_tm,trange):
    if from_tm is not None and to_tm is not None :        
        # check time                                      
        from_tm = "'{}'".format(from_tm)                  
        to_tm   = "'{}'".format(to_tm)                    
    else:                                                 
        from_tm = "now() - {}".format(trange)             
        to_tm   = "now()"  
    return from_tm,to_tm                               


@router.get("/network/metrics/tps",response_model=DgtMetricResponse)
async def get_metrics_tps(request: Request,trange:str = "24h",tgroup:str = "2m",from_tm:str = None,to_tm:str = None, query: QueryValidatorHandler = Depends(getQueryValidator)):
    # select last(count) from "dgt_validator.executor.TransactionExecutorThread.transaction_execution_count" where time >= now() - 24h and time <= now() group by time(2m),"host" fill(none)
    # SELECT last("count") FROM "dgt_validator.publisher.BlockPublisher.blocks_published_count" WHERE time >= now() - 24h and time <= now() GROUP BY time(2m), "host" fill(none)&epoch=ms
    from_tm,to_tm = get_time_range(from_tm,to_tm,trange)
    QUERY_TPS = 'select last(count) from "{}" where time >= {} and time <= {} group by time({}),"host" fill(none)'
    TPS =   "dgt_validator.executor.TransactionExecutorThread.transaction_execution_count"  
    squery  = QUERY_TPS.format(TPS,from_tm,to_tm,tgroup) #f'from(bucket: "{BACKET}") |> range(start: -1h) |> filter(fn: (r) => r["_measurement"] == "{TPS}")'   
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
async def get_metrics_latency(request: Request,trange:str = "24h",tgroup:str = "2m",from_tm:str = None,to_tm:str = None,query: QueryValidatorHandler = Depends(getQueryValidator)):             
    LAT ="dgt_validator.interconnect.Interconnect.send_response_time"  
    from_tm,to_tm = get_time_range(from_tm,to_tm,trange)                                                                                                        
    QUERY_LAT = 'select last(count),max(count),min(count),mean(count) as avg from "{}" where time >= {} and time <= {} group by time({}),"host" fill(none)' 
    squery  = QUERY_LAT.format(LAT,from_tm,to_tm,tgroup) 
    results = []                                                                                                        
    try:     
        LOGGER.debug("get get latency data {}".format(squery))                                                                                                           
        result = client.query(squery)                                                                               
        results = list(result.get_points())                                                                         
    except Exception as ex:                                                                                             
        LOGGER.debug("get get data {}".format(ex))                                                                      
                                                                                                                        
                                                                                                           
    return query._wrap_response(                                                                              
        request,                                                                                              
        data=DgtMetricItems(values=results),                                                                                              
        metadata=query._get_metadata(request, None))   
                                                   



  
@router.get("/network/metrics/entropy",response_model=DgtMetricResponse)                                                                                                                                
async def get_metrics_entropy(request: Request,trange:str = "24h",tgroup:str = "2m",from_tm:str = None,to_tm:str = None,query: QueryValidatorHandler = Depends(getQueryValidator)):
    """
    Evaluates the degree of randomness and distribution of activity across the network, 
    which can serve as an indicator of the network's health and security.
    """                                       
    LAT ="dgt_validator.interconnect.Interconnect.send_response_time"                                                                                                          
    from_tm,to_tm = get_time_range(from_tm,to_tm,trange)
    squery  = QUERY_FMT.format(LAT,from_tm,to_tm,tgroup) 
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
                                                                                       
@router.get("/network/metrics/node_activity",response_model=DgtMetricResponse)                                                                                                                                
async def get_metrics_node_activity(request: Request,trange:str = "24h",tgroup:str = "2m",from_tm:str = None,to_tm:str = None,query: QueryValidatorHandler = Depends(getQueryValidator)):   
    """
    Analyzes the activity of individual nodes in the network,
    including the number of transactions produced and processed, 
    which helps to determine the degree of centralization of the network.
    """ 
    from_tm,to_tm = get_time_range(from_tm,to_tm,trange)                                   
    NACT = "dgt_rest_api.post_batches_count"                  
    QUERY_FMT_H = 'select last(count),host from "{}" where time >= {} and time <= {} group by time({}),"host" fill(none)'                                                                        
    squery  = QUERY_FMT_H.format(NACT,from_tm,to_tm,tgroup)                          
    results = []                                                            
    try:       
        LOGGER.debug("get squery {}".format(squery))                                                             
        result = client.query(squery)                                       
        results = list(result.get_points())                                 
    except Exception as ex:                                                 
        LOGGER.debug("get get data {}".format(ex))                          

    return query._wrap_response(                                                                                                                 
        request,                                                                                                                                 
        data=DgtMetricItems(values=results),                                                                                                                                 
        metadata=query._get_metadata(request, None)) 

@router.get("/network/metrics/active_users",response_model=DgtMetricResponse)                                                                                                                                
async def get_metrics_active_users(request: Request,trange:str = "24h",tgroup:str = "2m",from_tm:str = None,to_tm:str = None,query: QueryValidatorHandler = Depends(getQueryValidator)):  
    """
    Provides information about the number of active users in the system over a specific period,
    which is an important indicator of the health of the ecosystem.
    """                                     
    AUSR = "dgt_validator.chain.ChainController.block_num"                                                                                
    from_tm,to_tm = get_time_range(from_tm,to_tm,trange)
    squery  = QUERY_FMT.format(AUSR,from_tm,to_tm,tgroup)                                                                                        
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
                                                                                       
@router.get("/network/metrics/blockchain_size",response_model=DgtMetricResponse)                                                                                                                                
async def get_metrics_blockchain_size(request: Request,trange:str = "24h",tgroup:str = "2m",from_tm:str = None,to_tm:str = None,query: QueryValidatorHandler = Depends(getQueryValidator)):                                       
    BSZ = "dgt_validator.chain.ChainController.block_num"
    from_tm,to_tm = get_time_range(from_tm,to_tm,trange)
    squery  = QUERY_FMT.format(BSZ,from_tm,to_tm,tgroup) 
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

                                                                                       

                                                                                        
                                                                                       
