"""I23 - testes da politica HTTP em loopback, sem rede externa/segredos.

Separados dos testes E2E GoTrue I22: este suite valida parser e transporte.
Nunca interprete a identidade fake abaixo como autorizacao de negocio.
"""
import http.client
import json
import threading
import unittest

from backend.identity_boundary import Denied, IdentityUnavailable, InvalidCommand
from backend.s1_gateway_http_policy_local import serve_http_policy_local

TOKEN = "Bearer " + "a" * 30


class FakeGateway:
    def __init__(self):
        self.calls = []
        self.failure = None
        self.result = {"outcome": "LOCAL_POLICY_OK"}

    def invoke(self, auth, command, data):
        self.calls.append((auth, command, data))
        if self.failure:
            raise self.failure
        return self.result


class Sink:
    def __init__(self):
        self.events = []

    def emit(self, category, command):
        self.events.append((category, command))


class HttpPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gateway = FakeGateway()
        cls.sink = Sink()
        cls.server = serve_http_policy_local(cls.gateway,
                 max_requests=150, window_seconds=60, security_events=cls.sink)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=4)

    def setUp(self):
        self.gateway.calls.clear()
        self.gateway.failure = None
        self.gateway.result = {"outcome": "LOCAL_POLICY_OK"}
        self.sink.events.clear()

    def request(self, *, method="POST", path="/s1/reativar", body='{"operador_id":"ok"}',
                headers=None, skip_default=(), duplicate=()):
        con = http.client.HTTPConnection("127.0.0.1", self.server.server_address[1], timeout=5)
        con.putrequest(method, path, skip_host=True, skip_accept_encoding=True)
        d = {
            "Host": "127.0.0.1:" + str(self.server.server_address[1]),
            "Content-Type": "application/json",
            "Authorization": TOKEN,
            "Content-Length": str(len(body.encode("utf-8") if isinstance(body,str) else body)),
        }
        for key in skip_default:
            d.pop(key)
        for key,val in (headers or {}).items():
            d[key] = val
        for key,val in d.items():
            con.putheader(key,val)
        for key,val in duplicate:
            con.putheader(key,val)
        con.endheaders()
        if method == "POST" and body:
            con.send(body.encode() if isinstance(body,str) else body)
        response=con.getresponse()
        content=response.read()
        out=(response.status, json.loads(content.decode()), dict(response.getheaders()))
        con.close()
        return out

    def assert_status(self, expected, **kwargs):
        status, data, _ = self.request(**kwargs)
        self.assertEqual(status,expected,str(data))

    def test_01_post_valid_calls_adapter(self):
        self.assert_status(200)
        self.assertEqual(len(self.gateway.calls),1)
        self.assertEqual(self.gateway.calls[0][1],"reativar")

    def test_02_security_headers_and_no_cors(self):
        code, body, headers = self.request()
        self.assertEqual(code,200)
        self.assertEqual(headers["Cache-Control"],"no-store")
        self.assertEqual(headers["Pragma"],"no-cache")
        self.assertEqual(headers["X-Content-Type-Options"],"nosniff")
        self.assertEqual(headers["X-Frame-Options"],"DENY")
        self.assertEqual(headers["Referrer-Policy"],"no-referrer")
        self.assertNotIn("Access-Control-Allow-Origin",headers)

    def test_03_unknown_command_not_called(self):
        self.assert_status(404,path="/s1/deletar")
        self.assertFalse(self.gateway.calls)

    def test_04_query_route_not_called(self):
        self.assert_status(404,path="/s1/reativar?operador_id=x")
        self.assertFalse(self.gateway.calls)

    def test_05_other_methods_denied(self):
        for method in ("GET","PUT","PATCH","DELETE","OPTIONS"):
            self.assert_status(405,method=method,body="")
        self.assertFalse(self.gateway.calls)

    def test_06_missing_bearer(self):
        self.assert_status(400,skip_default=("Authorization",))
        self.assertFalse(self.gateway.calls)

    def test_07_malformed_bearer(self):
        self.assert_status(403,headers={"Authorization":"Basic abc"})
        self.assertFalse(self.gateway.calls)

    def test_08_duplicate_auth_header(self):
        self.assert_status(400,duplicate=(("Authorization", TOKEN),))
        self.assertFalse(self.gateway.calls)

    def test_09_duplicate_content_length(self):
        self.assert_status(400,duplicate=(("Content-Length","19"),))
        self.assertFalse(self.gateway.calls)

    def test_10_duplicate_host(self):
        self.assert_status(400,duplicate=(("Host","evil.example"),))
        self.assertFalse(self.gateway.calls)

    def test_11_bad_host(self):
        self.assert_status(400,headers={"Host":"attacker.invalid"})
        self.assertFalse(self.gateway.calls)

    def test_12_cross_origin(self):
        self.assert_status(403,headers={"Origin":"https://attacker.invalid"})
        self.assertFalse(self.gateway.calls)

    def test_13_null_origin(self):
        self.assert_status(403,headers={"Origin":"null"})
        self.assertFalse(self.gateway.calls)

    def test_14_reject_cookies(self):
        self.assert_status(400,headers={"Cookie":"session=anything"})
        self.assertFalse(self.gateway.calls)

    def test_15_reject_proxy_forgery(self):
        self.assert_status(400,headers={"X-Forwarded-For":"127.0.0.1"})
        self.assertFalse(self.gateway.calls)

    def test_16_reject_chunked_transfer(self):
        self.assert_status(400,headers={"Transfer-Encoding":"chunked"})
        self.assertFalse(self.gateway.calls)

    def test_17_content_type_must_be_exact(self):
        self.assert_status(415,headers={"Content-Type":"application/json; charset=utf-8"})
        self.assertFalse(self.gateway.calls)

    def test_18_missing_content_length(self):
        self.assert_status(400,skip_default=("Content-Length",))
        self.assertFalse(self.gateway.calls)

    def test_19_body_limit(self):
        self.assert_status(413,body='{"x":"' + "z"*1050 + '"}')
        self.assertFalse(self.gateway.calls)

    def test_20_json_duplicate_fields(self):
        self.assert_status(400,body='{"operador_id":"first","operador_id":"second"}')
        self.assertFalse(self.gateway.calls)

    def test_21_json_nan_rejected(self):
        self.assert_status(400,body='{"operador_id":NaN}')
        self.assertFalse(self.gateway.calls)

    def test_22_json_top_level_array_rejected(self):
        self.assert_status(400,body='["unexpected"]')
        self.assertFalse(self.gateway.calls)

    def test_23_json_invalid_utf8(self):
        self.assert_status(400,body=b'{"x":"\xff"}')
        self.assertFalse(self.gateway.calls)

    def test_24_gateway_invalid_command_mapped(self):
        self.gateway.failure=InvalidCommand("sensitive_payload")
        status, data, _ = self.request()
        self.assertEqual(status,400)
        self.assertNotIn("sensitive",str(data))

    def test_25_gateway_denied_mapped(self):
        self.gateway.failure=Denied("secret session UUID")
        status, data, _ = self.request()
        self.assertEqual(status,403)
        self.assertEqual(data["error"],"DENIED")

    def test_26_upstream_failure_closed(self):
        self.gateway.failure=IdentityUnavailable("dsn://private:pw")
        status, data, _ = self.request()
        self.assertEqual(status,503)
        self.assertNotIn("dsn",str(data))

    def test_27_unexpected_exception_closed(self):
        self.gateway.failure=RuntimeError("SECRET_PRIVATE_STRING")
        status, data, _ = self.request()
        self.assertEqual(status,503)
        self.assertNotIn("SECRET_PRIVATE_STRING",str(data))

    def test_28_non_dict_response_closed(self):
        self.gateway.result=["invalid"]
        self.assert_status(503)

    def test_29_events_without_auth_payload(self):
        self.assert_status(403,headers={"Authorization":"Basic secret_auth"})
        self.assertTrue(self.sink.events)
        self.assertEqual(self.sink.events[-1],("HTTP_AUTH_DENIED","reativar"))
        self.assertNotIn("secret_auth",str(self.sink.events))

    def test_30_rate_limit_before_adapter(self):
        gw=FakeGateway()
        limiter=serve_http_policy_local(gw,max_requests=2,window_seconds=60)
        t=threading.Thread(target=limiter.serve_forever,daemon=True)
        t.start()
        try:
            statuses=[]
            for _ in range(3):
                conn=http.client.HTTPConnection("127.0.0.1",limiter.server_address[1],timeout=5)
                request_body=b'{}'
                conn.request("POST","/s1/reativar",body=request_body,
                    headers={"Authorization":TOKEN,"Content-Type":"application/json"})
                res=conn.getresponse()
                statuses.append(res.status)
                res.read()
                conn.close()
            self.assertEqual(statuses,[200,200,429])
            self.assertEqual(len(gw.calls),2)
        finally:
            limiter.shutdown()
            limiter.server_close()
            t.join(timeout=4)


if __name__=="__main__":
    unittest.main(verbosity=2)
