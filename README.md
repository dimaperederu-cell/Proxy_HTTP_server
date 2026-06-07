# Proxy_HTTP_server
A lightweight, non‑blocking HTTP proxy written in Python. It listens for incoming HTTP requests (only http:// scheme), forwards them to the destination server on port 80 (or a custom port specified in the URL), and returns the response to the client. Each connection is handled in a separate thread.
Features
✅ Parses HTTP/1.x requests and rewrites the request line (removes http://host part).

✅ Forwards requests to the target server (port 80 by default, custom port from URL is supported).

✅ Returns the server’s response to the client.

✅ Logs every request with:

Timestamp

Client address

HTTP method

Target host:port + path

Response status code

Latency (time from receiving the request to sending the last byte back to the client, in milliseconds)

✅ Multithreaded – handles multiple clients concurrently.

✅ Basic error handling (400 Bad Request, 502 Bad Gateway).

Requirements
Python 3.6+

No external dependencies (only standard library).

Installation
Clone the repository or download http_proxy.py directly:

bash
git clone https://github.com/yourusername/yourrepo.git
cd yourrepo
Usage
Run the proxy script:

bash
python http_proxy.py
By default the proxy listens on 127.0.0.1:8888. You can change LOCAL_HOST and LOCAL_PORT inside the script.

Example
Configure your browser or HTTP client to use 127.0.0.1:8888 as a proxy. Then visit any http:// website. The proxy will log the request and forward it.

Sample log output (console + proxy.log):

text
[2026-06-07 12:34:56] HTTP-прокси запущен на 127.0.0.1:8888
[2026-06-07 12:34:57] Новое подключение от ('127.0.0.1', 54321)
[2026-06-07 12:34:57] Клиент ('127.0.0.1', 54321) -> GET example.com:80/
[2026-06-07 12:34:57] Ответ клиенту ('127.0.0.1', 54321) -> example.com статус 200 за 45.2 мс
Limitations
Only http:// scheme is supported (no HTTPS CONNECT method).

Does not handle persistent connections (closes after each request/response).

Simple buffer reading – may not work with very large bodies (e.g., file downloads) as it reads until EOF. For production use, consider streaming.

Configuration
Edit constants at the top of the script:

python
LOCAL_HOST = '127.0.0.1'   # Listening address
LOCAL_PORT = 8888          # Listening port
BUFFER_SIZE = 8192         # Socket buffer size
LOG_FILE = "proxy.log"     # Log file name
License
MIT (or specify your own).
