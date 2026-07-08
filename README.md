# Middleware Stack Service — Deploy to Render (free tier)

## Files in this folder
- `main.py` — the FastAPI app (request-context + scoped CORS + rate limit)
- `requirements.txt` — Python dependencies
- `Procfile` — tells Render how to start the app

## Steps

1. **Create a new GitHub repo** (e.g. `middleware-api`) and upload all 3
   files from this folder into the repo root.

2. **Go to https://render.com** → sign in.

3. Click **New +** → **Web Service** → connect the `middleware-api` repo.

4. Fill in:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free

5. **Before deploying, add two Environment Variables** (Render dashboard →
   your service → Environment):

   | Key           | Value                                                     |
   |---------------|------------------------------------------------------------|
   | `YOUR_EMAIL`  | your actual login email, e.g. `you@gmail.com`               |
   | `EXAM_ORIGIN` | the exact origin of the grader page (see below how to find) |

   **How to find EXAM_ORIGIN**: open the exam/grader page in your browser,
   open DevTools (F12) → Console tab → type `location.origin` → press
   Enter. Copy that exact string (e.g. `https://exam.someplatform.com`)
   into the `EXAM_ORIGIN` variable.

   If you don't set `EXAM_ORIGIN`, only the assigned origin
   (`https://app-d3vjnc.example.com`) will be allowed, and the grader's
   own browser-based CORS check may fail.

6. Click **Create Web Service**, wait for deploy to finish.

7. Test in your browser:
   `https://your-service.onrender.com/ping`
   You should see `{"email": "...", "request_id": "..."}`.

8. Paste the base URL into the grader field.

## Notes
- Free Render services sleep when idle — hit `/ping` once yourself first
  to wake it up before the grader tests it.
- CORS is intentionally NOT wide-open here — only the assigned origin and
  `EXAM_ORIGIN` get the `Access-Control-Allow-Origin` header, per spec.
