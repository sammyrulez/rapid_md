from fastapi import FastAPI

from rapid_md.routers import router as upload_router
from rapid_md.render import render_router


app = FastAPI()
app.include_router(upload_router)
app.include_router(render_router)


