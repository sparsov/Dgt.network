from .status.endpoints import router as v1_status
from .batches.endpoints import router as v1_batches
from .peers.endpoints import router as v1_peers
from .topology.endpoints import router as v1_topology
from .graph.endpoints import router as v1_graph
from .dag.endpoints import router as v1_dag
from .blocks.endpoints import router as v1_blocks
from .transactions.endpoints import router as v1_transactions
from .receipts.endpoints import router as v1_receipts
from .state.endpoints import router as v1_state
from .families.endpoints import router as v1_families
from .dec import v1_emission, v1_assets, v1_accounts, v1_payments, v1_consortium
from .crypto.endpoints import router as v1_crypto
from .monitoring.endpoints import router as v1_monitoring





