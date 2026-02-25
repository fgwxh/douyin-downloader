from fastapi import APIRouter
from .endpoints import accounts, settings, download, works, cookie, config, proxy

router = APIRouter()

router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
router.include_router(settings.router, prefix="/settings", tags=["settings"])
router.include_router(download.router, prefix="/download", tags=["download"])
router.include_router(works.router, prefix="/works", tags=["works"])
router.include_router(cookie.router, prefix="/cookie", tags=["cookie"])
router.include_router(config.router, prefix="/config", tags=["config"])
router.include_router(proxy.router, prefix="/proxy", tags=["proxy"])
