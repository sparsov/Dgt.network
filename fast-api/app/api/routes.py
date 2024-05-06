from fastapi import APIRouter

from .endpoints import router as create_user
from .v1 import (v1_status, v1_batches, v1_peers, v1_topology, v1_graph, v1_dag,
                 v1_blocks, v1_transactions, v1_receipts, v1_state, v1_families,
                 v1_emission, v1_assets, v1_accounts, v1_payments, v1_consortium
                 )


router = APIRouter()

router.include_router(create_user)
router.include_router(v1_status)
router.include_router(v1_state)
router.include_router(v1_batches)
router.include_router(v1_blocks)
router.include_router(v1_transactions)
router.include_router(v1_receipts)
router.include_router(v1_peers)
router.include_router(v1_topology)
router.include_router(v1_graph)
router.include_router(v1_dag)
router.include_router(v1_families)
router.include_router(v1_emission)
router.include_router(v1_assets)
router.include_router(v1_accounts)
router.include_router(v1_payments)
router.include_router(v1_consortium)


