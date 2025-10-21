from fastapi import FastAPI
from fastapi_middleware_astack import AsyncExitStackMiddleware

from rapid_md.router_api import router as api_router
from rapid_md.router_web import render_router


app = FastAPI()
# Aggiunta del middleware AsyncExitStack
app.add_middleware(AsyncExitStackMiddleware)

app.include_router(api_router)
app.include_router(render_router)
