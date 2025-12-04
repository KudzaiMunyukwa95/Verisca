# Verisca Backend Deployment Guide 🚀

This guide will walk you through deploying your Verisca backend to Render using GitHub Desktop.

## Phase 1: Push Code to GitHub

1.  **Open GitHub Desktop**
2.  **File** -> **Add Local Repository...**
3.  **Choose Path**: Select the `Verisca` folder: `C:\Users\kmunyukwa.AONZWARSHRE\Downloads\Verisca`
4.  Click **Add Repository**
5.  It will say "This directory does not appear to be a Git repository". Click **Create a Repository**
    *   **Name**: `verisca-backend` (or similar)
    *   **Git Ignore**: Select `Python` (or leave as None since we created one manually)
    *   Click **Create Repository**
6.  **Publish Repository** (Top right button)
    *   **Name**: `verisca-backend`
    *   **Description**: Verisca Agricultural Insurance Platform Backend
    *   **Keep this code private**: Checked (Recommended)
    *   Click **Publish Repository**

## Phase 2: Create Web Service on Render

1.  Go to your [Render Dashboard](https://dashboard.render.com/)
2.  Click **New +** -> **Web Service**
3.  **Connect a repository**:
    *   Find `verisca-backend` in the list (you might need to click "Configure account" to grant access if it's not there)
    *   Click **Connect**
4.  **Configure the Service**:
    *   **Name**: `verisca-backend`
    *   **Region**: `Oregon (US West)` (Same as your database)
    *   **Branch**: `main` (or `master`)
    *   **Root Directory**: `backend` (IMPORTANT: Type `backend` here)
    *   **Runtime**: `Python 3`
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port 10000`
    *   **Instance Type**: `Free`

5.  **Environment Variables** (Scroll down to "Environment Variables" section):
    *   Click **Add Environment Variable** for each of these:
    
    | Key | Value |
    | :--- | :--- |
    | `PYTHON_VERSION` | `3.11.9` |
    | `DATABASE_URL` | **Use the Internal Database URL** from your Render Database dashboard (starts with `postgres://...`) |
    | `SECRET_KEY` | `verisca-secret-key-production-change-this` (Or generate a new random string) |
    | `APP_NAME` | `Verisca API` |
    | `DEBUG` | `False` |

6.  Click **Create Web Service**

## Phase 3: Verify Deployment

1.  Render will start building your app. Watch the logs!
2.  It will install dependencies and then try to start the server.
3.  Once it says **"Live"**, click the URL at the top (e.g., `https://verisca-backend.onrender.com`)
4.  You should see: `{"message":"Verisca API","version":"1.0.0","status":"operational"}`
5.  Add `/api/docs` to the URL to see the Swagger UI.

## Troubleshooting

*   **Build Failed?** Check the logs. Usually it's a missing package in `requirements.txt`.
*   **Deploy Failed?** Check if `DATABASE_URL` is correct (Internal URL for Render-to-Render communication).
