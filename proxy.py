from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.parse
import ssl
import re

class ProxyHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        url = params.get('url', [''])[0]

        if not url:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Missing url parameter')
            return

        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36')
            req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
            req.add_header('Accept-Language', 'en-US,en;q=0.5')
            resp = urllib.request.urlopen(req, timeout=15, context=ctx)
            content = resp.read()
            content_type = ''

            for key, val in resp.getheaders():
                if key.lower() == 'content-type':
                    content_type = val

            if 'text/html' in content_type:
                html = content.decode('utf-8', errors='replace')
                base_url = url.rstrip('/') + '/'
                if '<head>' in html:
                    html = html.replace('<head>', '<head><base href="' + base_url + '">', 1)
                elif '<HEAD>' in html:
                    html = html.replace('<HEAD>', '<HEAD><base href="' + base_url + '">', 1)
                content = html.encode('utf-8')

            self.send_response(resp.getcode())
            skip = {'x-frame-options', 'content-security-policy', 'x-xss-protection',
                     'transfer-encoding', 'content-encoding', 'connection'}
            for key, val in resp.getheaders():
                if key.lower() not in skip:
                    self.send_header(key, val)
            self.end_headers()
            self.wfile.write(content)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.end_headers()
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(str(e).encode())

HTTPServer(('127.0.0.1', 8888), ProxyHandler).serve_forever()
