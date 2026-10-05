from k8sml.ops import router as ops_router
from fastapi import FastAPI, HTTPException
from k8sml.gate import InputError, check

app = FastAPI()
app.include_router(ops_router, prefix="/v1")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/check")
def post_check(body: dict):
    try:
        return check(body)
    except InputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
