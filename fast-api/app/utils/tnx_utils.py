import time
from dgt_sdk.protobuf.batch_pb2 import Batch,BatchHeader,BatchList
from dgt_sdk.protobuf.transaction_pb2 import Transaction,TransactionHeader

from app.utils.logger import logger as LOGGER
from app.utils.signing import signer
                                                                                   
                                                                                                                                     

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
