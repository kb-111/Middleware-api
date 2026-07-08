# """
# Middleware Stack — demonstrates:
#   1. Request-context propagation (X-Request-ID)
#   2. Scoped CORS (single allowed origin, no wildcard)
#   3. Per-client (X-Client-Id) rate limiting

# Assigned values:
#   Allowed CORS origin = https://app-d3vjnc.example.com
#   B (rate limit)      = 11 requests / 10 seconds

# IMPORTANT — set these two environment variables at deploy time:
#   YOUR_EMAIL      -> the email address /ping should return
#   EXAM_ORIGIN     -> the exact origin (scheme+host+port) of the grader page,
#                      e.g. https://exam.example.com  (open devtools console on
#                      the grader page and run `location.origin` to get it)
# Both the assigned origin and EXAM_ORIGIN will get the ACAO header; every
# other origin gets none.
# """

# import os
# import time
# import uuid
# import threading
# from collections import deque

# from fastapi import FastAPI, Request
# from fastapi.responses import JSONResponse

# # --------------------------------------------------------------------------
# # Config
# # --------------------------------------------------------------------------
# ASSIGNED_ORIGIN = "https://app-d3vjnc.example.com"
# EXAM_ORIGIN = os.environ.get("EXAM_ORIGIN", "")   # set this at deploy time
# ALLOWED_ORIGINS = {o for o in (ASSIGNED_ORIGIN, EXAM_ORIGIN) if o}

# YOUR_EMAIL = os.environ.get("YOUR_EMAIL", "you@example.com")

# RATE_LIMIT = 11         # requests
# RATE_WINDOW = 10.0      # seconds

# app = FastAPI(title="Middleware Stack Service")

# _lock = threading.Lock()
# rate_buckets: dict[str, deque] = {}


# # --------------------------------------------------------------------------
# # Rate limiting helper (sliding window log)
# # --------------------------------------------------------------------------
# def check_rate_limit(client_id: str):
#     now = time.time()
#     with _lock:
#         bucket = rate_buckets.setdefault(client_id, deque())
#         while bucket and now - bucket[0] > RATE_WINDOW:
#             bucket.popleft()
#         if len(bucket) >= RATE_LIMIT:
#             oldest = bucket[0]
#             retry_after = max(1, int(RATE_WINDOW - (now - oldest)) + 1)
#             return retry_after
#         bucket.append(now)
#         return None


# # --------------------------------------------------------------------------
# # Single combined middleware: request-context -> rate-limit -> CORS headers
# # (Handling CORS by hand, not CORSMiddleware, so we can enforce an exact
# #  origin allowlist with no wildcard and still attach headers to 429s etc.)
# # --------------------------------------------------------------------------
# @app.middleware("http")
# async def stack_middleware(request: Request, call_next):
#     origin = request.headers.get("origin")
#     cors_headers = {}
#     if origin and origin in ALLOWED_ORIGINS:
#         cors_headers["Access-Control-Allow-Origin"] = origin
#         cors_headers["Vary"] = "Origin"
#         cors_headers["Access-Control-Allow-Credentials"] = "true"

#     # Handle CORS preflight directly.
#     if request.method == "OPTIONS":
#         headers = {
#             **cors_headers,
#             "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
#             "Access-Control-Allow-Headers": "*",
#             "Access-Control-Max-Age": "600",
#         }
#         return JSONResponse(content={}, status_code=200, headers=headers)

#     # --- Request-context (X-Request-ID) ---
#     request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
#     request.state.request_id = request_id

#     # --- Rate limiting per X-Client-Id ---
#     client_id = request.headers.get("X-Client-Id")
#     if client_id:
#         retry_after = check_rate_limit(client_id)
#         if retry_after is not None:
#             headers = {
#                 **cors_headers,
#                 "X-Request-ID": request_id,
#                 "Retry-After": str(retry_after),
#             }
#             return JSONResponse(
#                 content={"detail": "Rate limit exceeded", "request_id": request_id},
#                 status_code=429,
#                 headers=headers,
#             )

#     response = await call_next(request)

#     response.headers["X-Request-ID"] = request_id
#     for k, v in cors_headers.items():
#         response.headers[k] = v

#     return response


# # --------------------------------------------------------------------------
# # Endpoint
# # --------------------------------------------------------------------------
# @app.get("/ping")
# def ping(request: Request):
#     return {"email": YOUR_EMAIL, "request_id": request.state.request_id}


# @app.get("/")
# def root():
#     return {"status": "ok", "service": "middleware-stack"}
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