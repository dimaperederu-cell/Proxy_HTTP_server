# Proxy_HTTP_server
A lightweight, non‑blocking HTTP proxy written in Python. It listens for incoming HTTP requests (only http:// scheme), forwards them to the destination server on port 80 (or a custom port specified in the URL), and returns the response to the client. Each connection is handled in a separate thread.
