import time
from dgt_sdk.protobuf.batch_pb2 import Batch,BatchHeader,BatchList
from dgt_sdk.protobuf.transaction_pb2 import Transaction,TransactionHeader

from app.utils.logger import logger as LOGGER
from app.utils.signing import signer, _context
import base64                                                                                   
                                                                                                                                     
EMITTER  = "emitter"                                                                                                                                              
PAYLOAD_SIGNATURE   =  "signature"                                                                                                                                  
PAYLOAD = "payload"         
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
        timestamp=int(time.time()*1000)                                                        
        )                                                                                 
    return batch
                                                                          

def decode_signed(signed):
    payload = base64.b64decode(signed[PAYLOAD])                  
    designed = {                                                     
            EMITTER           : signed[EMITTER],             
            PAYLOAD_SIGNATURE : signed[PAYLOAD_SIGNATURE],           
            PAYLOAD           : payload                        
        }  
    ret = signer.verify(signed[PAYLOAD_SIGNATURE], payload,_context.pub_from_hex(signed[EMITTER]) )    
    if not ret:                                                                                      
        print('BAD SIGN')                                                                            


    LOGGER.debug('make_asset_trans CHECK={} payload={}'.format(ret,designed)) 
    return designed,signed[EMITTER]   
                                                                          
