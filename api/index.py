from fastapi import FastAPI, Request
from api.auth import router as auth_router
from api.notes import router as notes_router

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.include_router(auth_router)
app.include_router(notes_router)


@app.middleware("http")
async def prevent_api_caching(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "private, no-store"
    return response
