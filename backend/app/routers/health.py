from fastapi import APIRouter
router = APIRouter()
@router.get('/api/health')
@router.get('/health')
def health():
    return {'ok': True, 'service': 'atmosphere', 'stage': 2}
