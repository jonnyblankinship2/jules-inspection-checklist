# Serving the Frontend Locally

To run this frontend application and allow it to correctly communicate with the backend API (avoiding CORS issues that arise from `file:///` URLs), you need to serve these files from a simple local HTTP server.

Choose one of the methods below:

## Method 1: Using Python (if Python is installed)

1.  Navigate to this `frontend` directory in your terminal:
    ```bash
    cd path/to/your/fire-equipment-app/frontend
    ```

2.  Run Python's built-in HTTP server.

    For Python 3:
    ```bash
    python -m http.server 8080
    ```
    (You can use any port other than the one your backend is running on, e.g., 5000 for Flask).

    For Python 2 (less common now):
    ```bash
    python -m SimpleHTTPServer 8080
    ```

3.  Open your web browser and go to:
    `http://localhost:8080`

## Method 2: Using Node.js (if Node.js and npm/npx are installed)

1.  Navigate to this `frontend` directory in your terminal:
    ```bash
    cd path/to/your/fire-equipment-app/frontend
    ```

2.  Use `npx` (which comes with npm 5.2+) to run the `serve` package:
    ```bash
    npx serve -l 8080
    ```
    (The `-l 8080` flag tells it to listen on port 8080. You can change the port.)
    If you don't have `npx` or want to install `serve` globally:
    ```bash
    npm install -g serve
    serve -l 8080
    ```
    
3.  Open your web browser and go to:
    `http://localhost:8080`

## Important Notes:

*   **Backend Server:** Ensure your backend Flask server is running (usually on a different port, e.g., `http://localhost:5000`).
*   **CORS:** The backend has been configured with `Flask-CORS` to allow requests from `http://localhost:8080` (or whichever port you serve the frontend on, though the current CORS setup on backend is `*` for development).
*   **API Calls:** The frontend `app.js` makes API calls to relative paths like `/api/...` or `/auth/...`. When served via `http.server` or `serve`, these will correctly target your backend at `http://localhost:5000` (or your configured backend port) assuming the browser is also on `localhost`. If your backend is on a different host/port visible to your browser, the `fetch` calls in `app.js` might need to be updated to use absolute URLs (e.g., `http://your-backend-host:5000/api/...`). For typical local development, relative paths work fine when both are on `localhost`.
