"""Loopback harness ONLY. No Meta listener, external ACK mapping or productive 200."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .protocol import canonical, strict_json, unb64

def serve(ingress, *, drop_response=False):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):
            pass  # Never log request body, identity or credentials.
        def do_POST(self):
            if self.path != '/lab/ingress':
                self.send_error(404)
                return
            try:
                length = int(self.headers.get('Content-Length','0'))
                if not 0 < length <= 490000:
                    raise ValueError()
                packet = strict_json(self.rfile.read(length))
                if set(packet) != {'envelope','signature'}:
                    raise ValueError()
                result = ingress.call(unb64(packet['envelope']),packet['signature'])
                if drop_response:
                    self.close_connection = True
                    return
                status = {'ACK_ELIGIBLE':207,'REJECTED':422,'CONFLICT':409,
                          'PENDING_RECONCILIATION':503,'UNAVAILABLE':503}[result['decision']]
                data = canonical(result)
                self.send_response(status)
                self.send_header('Content-Type','application/json')
                self.send_header('Content-Length',str(len(data)))
                self.send_header('X-Prumo-Laboratory-Only','true')
                self.end_headers()
                self.wfile.write(data)
            except Exception:
                self.send_error(400,'LAB_INVALID_PACKET')
    return ThreadingHTTPServer(('127.0.0.1',0),Handler)
