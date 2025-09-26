# app/mainapi.py
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from app.database import Base, engine

from app.routers import (
    auth,
    projects,
    materials,
    vendors,
    boq,
    quotations,
    purchase_orders,
    payments,
    deliveries,
    qrcode,
)

app = FastAPI(title="Procurement Chatbot API", description="Procurement Chatbot API")

@app.on_event("startup")
def on_startup():
    # import models so SQLAlchemy sees them, then create tables if missing
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)


# ---- Routers (core ones) ----
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(projects.router, prefix="/projects", tags=["Projects"])
app.include_router(materials.router, prefix="/materials", tags=["Materials"])
app.include_router(vendors.router, prefix="/vendors", tags=["Vendors"])
app.include_router(boq.router, prefix="/boq", tags=["BOQ"])
app.include_router(quotations.router, prefix="/quotations", tags=["Quotations"])
app.include_router(purchase_orders.router, prefix="/purchase_orders", tags=["Purchase Orders"])
app.include_router(payments.router, prefix="/payments", tags=["Payments"])
app.include_router(deliveries.router, prefix="/deliveries", tags=["Deliveries"])
app.include_router(qrcode.router, prefix="/qrcode", tags=["QR Code"])


# -------------------------
# Custom OpenAPI generator
#  - Keeps components/schemas
#  - Filters each operation's responses to only include 2xx responses (where possible)
# -------------------------
def custom_openapi_keep_success_only():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version="1.0.0",
        description=getattr(app, "description", None) or "Procurement Chatbot API",
        routes=app.routes,
    )

    # Iterate paths and keep only 2xx responses where present
    paths = openapi_schema.get("paths", {})
    for path, methods in list(paths.items()):
        for method, details in list(methods.items()):
            responses = details.get("responses", {})
            # keep only responses where the status code string starts with '2'
            new_responses = {code: resp for code, resp in responses.items() if str(code).startswith("2")}
            if new_responses:
                details["responses"] = new_responses
            else:
                # fallback: if 200 exists keep it; otherwise leave responses as-is
                if "200" in responses:
                    details["responses"] = {"200": responses["200"]}

    # preserve components (schemas) as-is
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi_keep_success_only
