from fastapi import FastAPI

from rapid_md.routers import router as upload_router

app = FastAPI()
app.include_router(upload_router)

def main():
    print("Hello from rapid-md!")
def main():
    print("Hello from rapid-md!")


if __name__ == "__main__":
    main()
