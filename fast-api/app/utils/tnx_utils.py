import time
from dgt_sdk.protobuf.batch_pb2 import Batch,BatchHeader,BatchList
from dgt_sdk.protobuf.transaction_pb2 import Transaction,TransactionHeader

from app.utils.logger import logger as LOGGER
from app.utils.signing import signer
import base64                                                                                   
                                                                                                                                     

def create_batch(transactions,signer):                                                    
    """                                                                                   
    Create batch for transactions                                                         
    """                                                                                   
    transaction_signatures = [t.header_signature for t in transactions]                   
                                                                                          
    header = BatchHeader(                                                                 
        signer_public_key=signer.get_public_key().as_hex(),                         
        transaction_ids=transaction_signatures                                            
    ).SerializeToString()                                                                 
                                                                                          
    signature = signer.sign(header)                                                 
                                                                                          
    batch = Batch(                                                                        
        header=header,                                                                    
        transactions=transactions,                                                        
        header_signature=signature,                                                       
        timestamp=int(time.time())                                                        
        )                                                                                 
    return batch
                                                                          

def decode_signed(signed):
    payload = base64.b64decode(signed["payload"])                  
    designed = {                                                     
            DEC_EMITTER           : signed["emitter"],             
            DEC_PAYLOAD_SIGNATURE : signed["signature"],           
            DEC_PAYLOAD           : payload                        
        }  
    ret = signer.verify(signed["signature"], payload,_context.pub_from_hex(signed["emitter"]) )    
    if not ret:                                                                                      
        print('BAD SIGN')                                                                            


    LOGGER.debug('make_asset_trans CHECK={} payload={}'.format(ret,designed)) 
    return designed,signed["emitter"]   
                                                                          
