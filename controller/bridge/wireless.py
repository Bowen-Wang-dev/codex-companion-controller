"""Authenticated HTTPS transport. Pair secrets are local, never Codex credentials."""
import hmac
import json
from pathlib import Path
import socket
import ssl
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import threading

PRIVATE = Path(__file__).resolve().parents[1] / 'private'
DEVICE_RESPONSE_BYTES = 4096


def encode_snapshot(snapshot):
    """Bound the wire frame without ever truncating approval scope/details."""
    response = json.dumps(snapshot, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    if len(response) >= DEVICE_RESPONSE_BYTES:
        # History is presentation data; omit it only when the frame is oversized.
        # Preserve every permission/review/binding field and its exact value.
        snapshot = dict(snapshot, history=[])
        response = json.dumps(snapshot, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    if len(response) >= DEVICE_RESPONSE_BYTES:
        raise ValueError('Snapshot exceeds device buffer')
    return response


class DeviceHTTPServer(ThreadingHTTPServer):
    """Accept raw TCP immediately; a stalled TLS handshake owns only its worker."""
    daemon_threads = True
    request_queue_size = 16

    def process_request_thread(self, request, client_address):
        connection = request
        try:
            request.settimeout(3)
            request.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            connection = self.tls_context.wrap_socket(request, server_side=True)
            # wrap_socket takes ownership of the descriptor. Configure the
            # actual TLS socket too, instead of only the detached raw socket.
            connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            # Also bound idle keep-alive connections and incomplete HTTP bodies.
            connection.settimeout(10)
        except (OSError, ValueError):
            self.shutdown_request(connection)
            return
        super().process_request_thread(connection, client_address)

    def handle_error(self, request, client_address):
        # HTTP bodies/headers and credentials must never appear in tracebacks.
        print('无线 HTTP 请求未完成；等待设备重连。', flush=True)


def start_https(broker, port=8765):
    config_path = PRIVATE / 'wireless.json'
    if not config_path.exists():
        print('无线未配对：运行「配置无线连接.command」。USB 仍可使用。', flush=True)
        return None
    config = json.loads(config_path.read_text())

    class Handler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'

        def log_message(self, *args):
            pass  # Never log tokens or request bodies.

        def do_POST(self):
            authorized = hmac.compare_digest(self.headers.get('Authorization', ''),
                                             'Bearer ' + config['token'])
            try:
                length = int(self.headers.get('Content-Length', '0'))
            except ValueError:
                self.send_error(400)
                self.close_connection = True
                return
            if not authorized or self.path != '/device' or not 0 < length < 4096:
                self.send_error(403)
                self.close_connection = True
                return
            try:
                raw = self.rfile.read(length)
                if len(raw) != length:
                    self.close_connection = True
                    return
                message = json.loads(raw)
                if not isinstance(message, dict):
                    raise ValueError('Object required')
                broker.device_message(message, 'wifi')
                # UTF-8 keeps readable Chinese within the fixed firmware buffer.
                snapshot = broker.snapshot()
            except (ValueError, TypeError, KeyError):
                self.send_error(400)
                self.close_connection = True
                return
            try:
                response = encode_snapshot(snapshot)
            except ValueError:
                print('无线快照超出设备缓冲区；未发送不完整审批详情。', flush=True)
                self.send_error(503)
                self.close_connection = True
                return
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(response)
            self.wfile.flush()

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.maximum_version = ssl.TLSVersion.TLSv1_2
    ctx.set_ecdh_curve('prime256v1')
    ctx.load_cert_chain(str(PRIVATE / 'bridge-cert.pem'), str(PRIVATE / 'bridge-key.pem'))
    server = DeviceHTTPServer(('0.0.0.0', port), Handler)
    server.tls_context = ctx
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f'加密无线 Bridge 已启动：HTTPS {port}，需要已配对设备。', flush=True)
    return server
