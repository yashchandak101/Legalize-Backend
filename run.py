import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("BACKEND_PORT", 3000))
    print(f"Starting backend on port {port}", flush=True)
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
    )