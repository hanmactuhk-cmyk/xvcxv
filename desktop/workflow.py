import json
from pathlib import Path

SOCKETS={
'prompt':([],['string']), 'batch_prompt':([],['string']), 'reference':([],['image']), 'batch_loader':([],['image']),
'frame_extract':(['video'],['image']), 'render':(['video','video'],['video']),
'generate':(['string'],['image']), 'video_generate':(['string'],['video']), 'grok':(['string'],['any']), 'meta':(['string'],['any']), 'openai':(['string'],['image'])}

def _mode_inputs(node):
    t=node.get('type'); mode=node.get('values',{}).get('mode')
    if t=='video_generate':
        if mode=='image': return ['string','image','image']
        return ['string']+['image']*max(0,len(node.get('inputs',[]))-1)
    if t=='grok': return ['string']+['image']*max(0,len(node.get('inputs',[]))-1) if mode in ('i2i','i2v') else ['string']
    if t=='meta':
        if mode=='i2i': return ['string']+['image']*max(0,len(node.get('inputs',[]))-1)
        if mode=='i2v': return ['string','image','image']
        return ['string']
    if t in ('generate','openai'):
        return ['string']+['image']*max(0,len(node.get('inputs',[]))-1)
    return SOCKETS.get(t,([],[]))[0]

def validate(doc, check_files=True):
    errors=[]; warnings=[]
    if not isinstance(doc,dict): return ['Workflow root must be an object'],[]
    nodes=doc.get('nodes'); edges=doc.get('edges'); groups=doc.get('groups',[])
    if not isinstance(nodes,list): errors.append('nodes must be an array')
    if not isinstance(edges,list): errors.append('edges must be an array')
    if not isinstance(groups,list): errors.append('groups must be an array')
    if errors: return errors,warnings
    ids=set()
    for i,n in enumerate(nodes):
        if not isinstance(n,dict): errors.append(f'node {i}: must be an object'); continue
        for k in ('id','type','title','x','y','inputs','outputs','values'):
            if k not in n: errors.append(f'node {i}: missing {k}')
        if n.get('id') in ids: errors.append(f'node {i}: duplicate id {n.get("id")}')
        ids.add(n.get('id'))
        t=n.get('type')
        if t not in SOCKETS: errors.append(f'node {i}: unknown type {t}'); continue
        ins=_mode_inputs(n)
        if len(n.get('inputs',[]))!=len(ins): errors.append(f'node {i}: inputs count {len(n.get("inputs",[]))} != expected {len(ins)} for mode')
        if t in ('prompt','batch_prompt','reference','batch_loader') and len(n.get('inputs',[]))!=0: errors.append(f'node {i}: {t} must have zero inputs')
        if t=='reference' and check_files:
            p=n.get('values',{}).get('file_path');
            if p and not Path(p).exists(): warnings.append(f'node {i}: reference file does not exist: {p}')
        if t=='batch_loader' and check_files:
            p=n.get('values',{}).get('file_path');
            if p and not Path(p).is_dir(): warnings.append(f'node {i}: batch folder does not exist: {p}')
    for j,e in enumerate(edges):
        try: a,b,c,d=e['start_node'],e['start_socket'],e['end_node'],e['end_socket']
        except Exception: errors.append(f'edge {j}: invalid fields'); continue
        if not all(isinstance(x,int) for x in (a,b,c,d)): errors.append(f'edge {j}: node/socket indexes must be integers'); continue
        if not (0<=a<len(nodes) and 0<=c<len(nodes)): errors.append(f'edge {j}: node index out of range'); continue
        outs=SOCKETS.get(nodes[a].get('type'),([],[]))[1]
        if b<0 or (outs and b>=len(outs)): warnings.append(f'edge {j}: start socket {b} may be invalid')
        ins=_mode_inputs(nodes[c])
        if d<0 or d>=len(ins): errors.append(f'edge {j}: end socket {d} invalid for node {c}')
        elif outs:
            src=outs[b] if 0<=b<len(outs) else 'any'; dst=ins[d]
            if src!='any' and dst!='any' and src!=dst: errors.append(f'edge {j}: incompatible {src} -> {dst}')
    seen=set()
    for e in edges:
        key=(e.get('end_node'),e.get('end_socket'))
        if key in seen and 0<=key[0]<len(nodes) and _mode_inputs(nodes[key[0]])[key[1]]=='string': errors.append(f'prompt socket {key[0]} has multiple incoming edges')
        seen.add(key)
    # cycle check
    g={i:[] for i in range(len(nodes))}
    for e in edges:
        if isinstance(e,dict) and isinstance(e.get('start_node'),int) and isinstance(e.get('end_node'),int) and e['start_node'] in g and e['end_node'] in g: g[e['start_node']].append(e['end_node'])
    state=[0]*len(nodes)
    def dfs(v):
        state[v]=1
        for w in g[v]:
            if state[w]==1: return True
            if state[w]==0 and dfs(w): return True
        state[v]=2; return False
    if any(state[i]==0 and dfs(i) for i in range(len(nodes))): errors.append('workflow contains a cycle')
    return errors,warnings

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))
def save(doc,path):
    Path(path).write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding='utf-8')
