import http.client
import json
import unittest

from sessionglow.server import Server


class ServerTest(unittest.TestCase):
    def setUp(self):
        self.server = Server(0)
        self.server.start()
        self.addCleanup(self.server.close)

    def request(self, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.port, timeout=3)
        connection.request("GET" if body is None else "POST", path, body, headers or {})
        result = connection.getresponse()
        status, raw = result.status, result.read()
        connection.close()
        return status, raw

    def test_receive_and_health(self):
        self.assertEqual(self.request("/opencode", b'{"instance_id":"a","sequence":1,"sessions":[]}')[0], 204)
        self.assertEqual(self.server.events.get(timeout=1)["instance_id"], "a")
        status, raw = self.request("/health")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw)["app"], "SessionGlow")

    def test_reject_invalid_requests(self):
        for payload in (b"[]", b"null", b"{", b"\xff"):
            self.assertEqual(self.request("/opencode", payload)[0], 400)
        self.assertEqual(self.request("/opencode", b"{}", {"Origin": "https://example.com"})[0], 403)
        self.assertEqual(self.request("/opencode", b"{}", {"Content-Length": "9999999"})[0], 413)
        self.assertTrue(self.server.events.empty())
