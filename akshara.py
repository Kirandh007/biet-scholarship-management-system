import os
from http.server import ThreadingHTTPServer
from portal import APP, H, seed


if __name__ == "__main__":
    seed()
    port = int(os.getenv("PORT", "8000"))
    print(f"{APP} running on port {port}")
    ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()
