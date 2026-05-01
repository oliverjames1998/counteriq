from fastapi import FastAPI

from .routers import cameras, edge, events, me, stores, zones

app = FastAPI(title="CounterIQ API", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}


app.include_router(me.router)
app.include_router(stores.router)
app.include_router(cameras.router)
app.include_router(zones.router)
app.include_router(events.router)
app.include_router(edge.router)
