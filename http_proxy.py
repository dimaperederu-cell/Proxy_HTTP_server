#!/usr/bin/env python3
"""
Простой многопоточный HTTP-прокси.
Особенности:
- Принимает соединения на LOCAL_HOST:LOCAL_PORT
- Парсит HTTP-запросы клиентов (только схема http://)
- Устанавливает соединение с целевым сервером (порт 80)
- Пересылает запрос, получает ответ, возвращает клиенту
- Логирует: время, метод, URL, статус ответа, задержку в мс
- Замер задержки: от получения запроса до отправки последнего байта клиенту

Запуск: python http_proxy.py
"""

import socket
import threading
import time
import re
from datetime import datetime

# ==================== КОНФИГУРАЦИЯ ====================
LOCAL_HOST = '127.0.0.1'
LOCAL_PORT = 8888
BUFFER_SIZE = 8192
LOG_FILE = "proxy.log"

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def log(message):
    """Вывод в консоль и запись в файл с временной меткой"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {message}"
    print(full_msg)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(full_msg + '\n')

def parse_request(request_data):
    try:
        first_line = request_data.split(b'\r\n')[0].decode('ascii', errors='ignore')
        parts = first_line.split(' ')
        if len(parts) < 3:
            return None, None, 80, None
        method, full_url, _ = parts[0], parts[1], parts[2]

        match = re.match(r'http://([^/:]+)(?::(\d+))?(/.*)?', full_url)
        if not match:
            return None, None, 80, None
        host = match.group(1)
        port_str = match.group(2) if match.group(2) else '80'
        port = int(port_str)
        path = match.group(3) if match.group(3) else '/'
        return method, host, port, path
    except Exception:
        return None, None, 80, None

def forward_request(client_socket, request_data, host, port, path):
    """
    Отправляет запрос на целевой сервер и возвращает ответ.
    При необходимости корректирует строку запроса (убирает http://host).
    """
    # Модифицируем первую строку: убираем http://host, оставляем только path
    lines = request_data.split(b'\r\n')
    first_line = lines[0].decode('ascii', errors='ignore')
    # Заменяем полный URL на path
    new_first_line = re.sub(r'http://[^/]+', '', first_line)
    lines[0] = new_first_line.encode()
    modified_request = b'\r\n'.join(lines)

    try:
        # Подключаемся к целевому серверу
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.settimeout(10.0)
        server_socket.connect((host, port))
        server_socket.sendall(modified_request)

        # Получаем ответ от сервера
        response = b''
        while True:
            chunk = server_socket.recv(BUFFER_SIZE)
            if not chunk:
                break
            response += chunk
        server_socket.close()
        return response
    except Exception as e:
        log(f"Ошибка соединения с {host}:{port} - {e}")
        return None

def handle_client(client_socket, client_addr):
    """
    Обрабатывает одно клиентское соединение.
    Читает запрос, парсит, пересылает, замеряет задержку, логирует.
    """
    start_time = time.time()
    try:
        # Принимаем данные от клиента (упрощённо - читаем до закрытия или таймаута)
        client_socket.settimeout(5.0)
        request_data = b''
        while True:
            chunk = client_socket.recv(BUFFER_SIZE)
            if not chunk:
                break
            request_data += chunk
            # Останавливаемся, если получили конец заголовков (два \r\n\r\n)
            if b'\r\n\r\n' in request_data:
                break

        if not request_data:
            client_socket.close()
            return

        # Парсим запрос
        method, host, port, path = parse_request(request_data)
        if not host:
            # Неподдерживаемый запрос (например, CONNECT для HTTPS)
            log(f"Клиент {client_addr} прислал неподдерживаемый запрос: {request_data[:100]}")
            client_socket.send(b'HTTP/1.1 400 Bad Request\r\n\r\n')
            client_socket.close()
            return

        log(f"Клиент {client_addr} -> {method} {host}:{port}{path}")

        # Пересылаем запрос на целевой сервер
        response = forward_request(client_socket, request_data, host, port, path)
        if response is None:
            # Если не удалось получить ответ, отдаём ошибку
            client_socket.send(b'HTTP/1.1 502 Bad Gateway\r\n\r\n')
            client_socket.close()
            return

        # Отправляем ответ клиенту
        client_socket.sendall(response)

        # Измеряем общую задержку (от получения запроса до отправки ответа)
        elapsed_ms = (time.time() - start_time) * 1000

        # Пытаемся извлечь статус из ответа для логирования
        status_line = response.split(b'\r\n')[0] if response else b''
        status_code = status_line.split(b' ')[1] if len(status_line.split(b' ')) > 1 else b'???'
        log(f"Ответ клиенту {client_addr} -> {host} статус {status_code.decode()} за {elapsed_ms:.1f} мс")

    except socket.timeout:
        log(f"Клиент {client_addr} таймаут")
    except Exception as e:
        log(f"Ошибка при обработке клиента {client_addr}: {e}")
    finally:
        client_socket.close()

# ==================== ЗАПУСК ПРОКСИ ====================
def start_proxy():
    """Запускает прокси-сервер, слушающий LOCAL_HOST:LOCAL_PORT."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((LOCAL_HOST, LOCAL_PORT))
    server_socket.listen(5)
    log(f"HTTP-прокси запущен на {LOCAL_HOST}:{LOCAL_PORT}")

    try:
        while True:
            client_sock, client_addr = server_socket.accept()
            log(f"Новое подключение от {client_addr}")
            # Создаём поток для каждого клиента
            client_thread = threading.Thread(target=handle_client, args=(client_sock, client_addr))
            client_thread.daemon = True
            client_thread.start()
    except KeyboardInterrupt:
        log("Завершение работы прокси по Ctrl+C")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_proxy()