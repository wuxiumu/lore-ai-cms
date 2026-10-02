"""Normalize Anthropic/OpenAI response and usage without logging credentials."""
import json,time,urllib.request,urllib.error,re
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None
class ModelError(RuntimeError): pass

def call(provider,system,payload,max_tokens=4500):
    protocol=provider['protocol'];base=provider['base_url'].rstrip('/')
    headers={'Content-Type':'application/json'}
    content=json.dumps(payload,ensure_ascii=False)
    if protocol=='anthropic':
        endpoint=base+'/v1/messages'
        headers.update({'x-api-key':provider['api_key'],'anthropic-version':'2023-06-01'})
        body={'model':provider['model'],'system':system,'messages':[{'role':'user','content':content}],'max_tokens':max_tokens,'thinking':{'type':'disabled'}}
    else:
        endpoint=base+'/chat/completions';headers['Authorization']='Bearer '+provider['api_key']
        body={'model':provider['model'],'messages':[{'role':'system','content':system},{'role':'user','content':content}],'max_tokens':max_tokens,'temperature':.5,'thinking':{'type':'disabled'}}
    start=time.monotonic()
    try:
        req=urllib.request.Request(endpoint,data=json.dumps(body,ensure_ascii=False).encode(),headers=headers)
        with urllib.request.build_opener(NoRedirect).open(req,timeout=180) as r:raw=json.loads(r.read(4000000))
    except urllib.error.HTTPError as e:
        # Only output short error codes, never full provider bodies or request headers.
        try:
            err=json.loads(e.read(10000));code=err.get('error',{}).get('code',err.get('error',{}).get('type','unknown'))
        except Exception:code='unknown'
        raise ModelError(f'HTTP {e.code}; code={str(code)[:60]}') from None
    u=raw.get('usage') or {}
    if protocol=='anthropic':
        text=''.join(x.get('text','') for x in raw.get('content',[]) if x.get('type')=='text')
        reason=raw.get('stop_reason');inp=u.get('input_tokens');out=u.get('output_tokens')
    else:
        choice=raw['choices'][0];text=choice['message'].get('content') or '';reason=choice.get('finish_reason');inp=u.get('prompt_tokens');out=u.get('completion_tokens')
    usage={'provider':provider['provider'],'model_requested':provider['model'],'model_returned':raw.get('model'),'input_tokens':inp,'output_tokens':out,'total_tokens':u.get('total_tokens',inp+out if inp is not None and out is not None else None),'cache_read_input_tokens':u.get('cache_read_input_tokens',0),'cache_creation_input_tokens':u.get('cache_creation_input_tokens',0),'seconds':round(time.monotonic()-start,2),'stop_reason':reason}
    return text,usage

def json_result(text):
    text=re.sub(r'^```(?:json)?\s*|\s*```$','',text.strip())
    return json.loads(text,strict=False)
