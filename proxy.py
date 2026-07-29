from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.parse
import ssl
import re

class ProxyHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def handle_request(self, method):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        url = params.get('url', [''])[0]

        if not url:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Missing url parameter')
            return

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            req = urllib.request.Request(url, data=body, method=method)
            req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36')
            req.add_header('Accept', '*/*')
            req.add_header('Accept-Language', 'en-US,en;q=0.5')
            for key in ('Content-Type', 'Cookie', 'X-Requested-With', 'Origin', 'Referer'):
                val = self.headers.get(key)
                if val:
                    req.add_header(key, val)

            resp = urllib.request.urlopen(req, timeout=15, context=ctx)
            content = resp.read()
            content_type = ''
            for key, val in resp.getheaders():
                if key.lower() == 'content-type':
                    content_type = val.lower()

            parsed_url = urllib.parse.urlparse(url)
            origin = parsed_url.scheme + '://' + parsed_url.netloc

            if 'text/html' in content_type and method == 'GET':
                html = content.decode('utf-8', errors='replace')
                html = self.rewrite_html(html, origin)
                content = html.encode('utf-8')
            elif 'text/css' in content_type and method == 'GET':
                css = content.decode('utf-8', errors='replace')
                css = self.rewrite_css(css, origin)
                content = css.encode('utf-8')

            self.send_response(resp.getcode())
            skip = {'x-frame-options', 'content-security-policy', 'x-xss-protection',
                     'transfer-encoding', 'connection', 'content-encoding'}
            for key, val in resp.getheaders():
                if key.lower() not in skip:
                    self.send_header(key, val)
            self.end_headers()
            self.wfile.write(content)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for key, val in e.headers.items():
                if key.lower() not in ('x-frame-options', 'content-security-policy', 'transfer-encoding'):
                    self.send_header(key, val)
            self.end_headers()
            content = e.read()
            if content:
                self.wfile.write(content)
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(str(e).encode())

    def encode_url(self, url):
        return '/proxy?url=' + urllib.parse.quote(url, safe='')

    def get_nav_script(self, origin):
        return (
            '<script>'
            '(function(){'
            'var O="' + origin + '",P="/proxy?url=";'
            'function p(u){return u.indexOf(P)===0?u:P+encodeURIComponent(u)}'
            'document.addEventListener("click",function(e){'
            'var a=e.target.closest("a");'
            'if(!a||!a.href||a.protocol==="javascript:")return;'
            'var h=a.href;'
            'if(a.getAttribute("target")==="_blank")return;'
            'if(h.indexOf(O)===0){'
            'e.preventDefault();location.href=p(h)'
            '}else if(h.indexOf(location.origin)===0&&h.indexOf(P)!==0){'
            'e.preventDefault();location.href=p(h)'
            '}'
            '})'
            '})()'
            '</script>'
        )

    def get_fetch_script(self, origin):
        return (
            '<script>'
            '(function(){'
            'var O="' + origin + '",P="/proxy?url=";'
            'function p(u){'
            'if(u.indexOf(P)===0)return u;'
            'if(u.indexOf("http")===0)return P+encodeURIComponent(u);'
            'if(u.indexOf("//")===0)return u;'
            'if(u.indexOf("/")===0)return P+encodeURIComponent(O+u);'
            'return P+encodeURIComponent(O+"/"+u)'
            '}'
            'var _f=window.fetch;'
            'window.fetch=function(i,n){'
            'var u=i;'
            'if(typeof i==="string")u=i;'
            'else if(i&&i.url)u=i.url;'
            'else return _f.call(this,i,n);'
            'if(u.indexOf(P)===-1){return _f.call(this,p(u),n||{})}'
            'return _f.call(this,i,n)'
            '}'
            'var _o=XMLHttpRequest.prototype.open;'
            'XMLHttpRequest.prototype.open=function(m,u){'
            'if(typeof u==="string"&&u.indexOf(P)===-1){arguments[1]=p(u)}'
            'return _o.apply(this,arguments)'
            '}'
            '})()'
            '</script>'
        )

    def rewrite_html(self, html, origin):
        def rewrite_attr(match):
            prefix = match.group(1)
            quote = match.group(2)
            val = match.group(3)
            if val.startswith('/proxy?') or val.startswith('http') or val.startswith('data:') or val.startswith('#') or val.startswith('javascript:'):
                return match.group(0)
            if val.startswith('//'):
                return match.group(0)
            if val.startswith('/'):
                full = origin + val
            else:
                full = origin + '/' + val
            return prefix + quote + self.encode_url(full) + quote

        html = re.sub(r'((?:href|src|action|poster|srcset)\s*=\s*)(["\'])(/[^"\']*?)\2', rewrite_attr, html, flags=re.IGNORECASE)
        html = re.sub(r'url\(\s*["\']?\s*(/[^)"\']*)\s*["\']?\s*\)', lambda m: 'url(' + self.encode_url(origin + m.group(1)) + ')', html)

        scripts = self.get_nav_script(origin) + self.get_fetch_script(origin)
        html = html.replace('</head>', scripts + '</head>', 1)

        return html

    def rewrite_css(self, css, origin):
        def rewrite_url(match):
            val = match.group(1)
            if val.startswith('/proxy?') or val.startswith('http') or val.startswith('data:'):
                return match.group(0)
            if val.startswith('//'):
                return match.group(0)
            if val.startswith('/'):
                full = origin + val
            else:
                return match.group(0)
            return 'url(' + self.encode_url(full) + ')'

        return re.sub(r'url\(\s*["\']?\s*([^)"\']*)\s*["\']?\s*\)', rewrite_url, css)

    def do_GET(self): self.handle_request('GET')
    def do_POST(self): self.handle_request('POST')
    def do_PUT(self): self.handle_request('PUT')
    def do_DELETE(self): self.handle_request('DELETE')
    def do_PATCH(self): self.handle_request('PATCH')
    def do_HEAD(self): self.handle_request('HEAD')
    def do_OPTIONS(self): self.handle_request('OPTIONS')

HTTPServer(('127.0.0.1', 8888), ProxyHandler).serve_forever()
