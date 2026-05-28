from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = 8000

server = HTTPServer(("0.0.0.0", PORT), SimpleHTTPRequestHandler)

print(f"Freedeon server active on http://localhost:{PORT}")

server.serve_forever()
