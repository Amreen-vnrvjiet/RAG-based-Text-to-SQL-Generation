import http.server
import socketserver
import os

PORT = 8080
# Serve the directory where this script is located
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

# Bind specifically to 127.0.0.1 instead of default 0.0.0.0
try:
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        print("\n" + "="*50)
        print(" 🚀 Frontend Server Successfully Started!")
        print(f" 👉 Click here to open UI: http://127.0.0.1:{PORT}/")
        print("="*50 + "\n")
        print("Press Ctrl+C to stop the server.")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
except OSError as e:
    print(f"\n❌ Error starting server: Port {PORT} is likely already in use.")
    print("Please stop the existing 'python -m http.server 8080' process, and try again.")
