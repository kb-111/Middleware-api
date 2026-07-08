
import time
import uuid
import os
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()


# -----------------------------
# Configuration
# -----------------------------

EMAIL = os.getenv(
    "EMAIL",
    "24f1001928@ds.study.iitm.ac.in"
)

ALLOWED_ORIGINS = [
    "https://app-d3vjnc.example.com",
    # Add exam page origin here if provided
    "https://study.iitm.ac.in/ds/exam.html"
]

RATE_LIMIT = 11
WINDOW = 10


# -----------------------------
# Rate limiter storage
# -----------------------------

client_requests = defaultdict(deque)


# -----------------------------
# Middleware 1
# Request Context
# -----------------------------

@app.middleware("http")
async def request_context_middleware(request: Request, call_next):

    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


# -----------------------------
# Middleware 2
# Rate Limiter
# -----------------------------

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):

    client_id = request.headers.get(
        "X-Client-Id",
        "anonymous"
    )

    now = time.time()

    requests = client_requests[client_id]


    # Remove expired timestamps
    while requests and now - requests[0] > WINDOW:
        requests.popleft()


    if len(requests) >= RATE_LIMIT:

        return JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit exceeded"
            }
        )


    requests.append(now)


    response = await call_next(request)

    return response



# -----------------------------
# Middleware 3
# CORS
# -----------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=[
        "X-Client-Id",
        "X-Request-ID",
        "Content-Type"
    ],
)


# -----------------------------
# Endpoint
# -----------------------------

@app.get("/ping")
async def ping(request: Request):

    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }
