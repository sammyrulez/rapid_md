from fastapi import FastAPI

from rapid_md.router_api import router as api_router
from rapid_md.router_web import render_router


app = FastAPI()

app.include_router(api_router)
app.include_router(render_router)
