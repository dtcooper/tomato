from django.conf import settings

import uvicorn


uvicorn.run(
    "api:app",
    host="0.0.0.0",
    port=8000,
    workers=1,
    forwarded_allow_ips="*",
    proxy_headers=True,
    reload=settings.DEBUG,
)
