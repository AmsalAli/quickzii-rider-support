'''Health check endpoint. Trivial but useful for confirming the server is up
and for the agent to test connectivity before starting a session.'''
from fastapi import APIRouter

router = APIRouter(prefix='/health', tags=['health'])


@router.get('')
def health():
    return {'status': 'ok'}
