import json, time, urllib.request, urllib.error, urllib.parse
from pathlib import Path

class WebhookError(RuntimeError): pass

class WebhookClient:
    def __init__(self, base_url='http://127.0.0.1:8765', api_key=''):
        self.base_url=base_url.rstrip('/')
        self.api_key=api_key.strip()
    def _request(self, method, path, body=None, timeout=60):
        data=None
        headers={'Accept':'application/json'}
        if self.api_key: headers['X-API-Key']=self.api_key
        if body is not None:
            data=json.dumps(body).encode(); headers['Content-Type']='application/json'
        req=urllib.request.Request(self.base_url+path,data=data,headers=headers,method=method)
        try:
            with urllib.request.urlopen(req,timeout=timeout) as r:
                raw=r.read(); ct=r.headers.get('Content-Type','')
                return json.loads(raw) if 'json' in ct or raw[:1] in (b'{',b'[') else raw
        except urllib.error.HTTPError as e:
            raw=e.read().decode('utf-8','replace')
            raise WebhookError(f'HTTP {e.code}: {raw[:1000]}')
        except urllib.error.URLError as e:
            raise WebhookError(f'Connection failed: {e.reason}')
    def health(self): return self._request('GET','/api/health')
    def generate(self, kind, payload): return self._request('POST',f'/api/{kind}/generate',payload)
    def status(self, task_id): return self._request('GET',f'/api/status/{task_id}')
    def result(self, task_id): return self._request('GET',f'/api/result/{task_id}')
    def tasks(self): return self._request('GET','/api/tasks')
    def wait(self, task_id, interval=3, timeout=3600, on_update=None):
        started=time.time()
        while time.time()-started < timeout:
            s=self.status(task_id)
            if on_update: on_update(s)
            state=str(s.get('status',s.get('state',''))).lower()
            if state in ('completed','complete','success','succeeded','failed','error','cancelled'):
                if state in ('failed','error','cancelled'): raise WebhookError(str(s))
                return self.result(task_id)
            time.sleep(interval)
        raise WebhookError('Task polling timed out')
    def download(self, filename, destination):
        data=self._request('GET','/api/files/'+urllib.parse.quote(filename,safe=''))
        Path(destination).write_bytes(data if isinstance(data,bytes) else json.dumps(data).encode())
        return destination
