"""Authenticated HTTPS transport. Pair secrets are local, never Codex credentials."""
import hmac
import json
from pathlib import Path
import ssl
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import threading

PRIVATE=Path(__file__).resolve().parents[1]/'private'

def start_https(broker, port=8765):
    config_path=PRIVATE/'wireless.json'
    if not config_path.exists():
        print('无线未配对：运行「配置无线连接.command」。USB 仍可使用。',flush=True)
        return None
    config=json.loads(config_path.read_text())
    class Handler(BaseHTTPRequestHandler):
        protocol_version='HTTP/1.1'
        def log_message(self,*args): pass # Never log tokens or request bodies.
        def do_POST(self):
            authorized=hmac.compare_digest(self.headers.get('Authorization',''), 'Bearer '+config['token'])
            try:length=int(self.headers.get('Content-Length','0'))
            except ValueError:self.send_error(400); return
            if not authorized or self.path!='/device' or not 0<length<4096:
                self.send_error(403); self.close_connection=True; return
            try:
                message=json.loads(self.rfile.read(length))
                broker.device_message(message,'wifi')
                response=json.dumps(broker.snapshot(),separators=(',',':')).encode()
            except (ValueError,TypeError,KeyError): self.send_error(400); return
            self.send_response(200); self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(response))); self.end_headers(); self.wfile.write(response)
    server=ThreadingHTTPServer(('0.0.0.0',port),Handler)
    server.daemon_threads=True
    ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); ctx.minimum_version=ssl.TLSVersion.TLSv1_2
    ctx.maximum_version=ssl.TLSVersion.TLSv1_2
    ctx.set_ecdh_curve('prime256v1')
    ctx.load_cert_chain(str(PRIVATE/'bridge-cert.pem'),str(PRIVATE/'bridge-key.pem'))
    server.socket=ctx.wrap_socket(server.socket,server_side=True)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    print(f'加密无线 Bridge 已启动：HTTPS {port}，需要已配对设备。',flush=True)
    return server
