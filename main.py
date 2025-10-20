from fastapi import FastAPI

from rapid_md.routers import router as upload_router

app = FastAPI()
app.include_router(upload_router)


