"""Public recruitment page parser. CLI and optional FastMCP entrypoint."""
import argparse, asyncio, ipaddress, json, re, socket
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

TRACKING = {'oem_code','logpath','stext','listno','sc','utm_source','utm_medium','utm_campaign','utm_content','utm_term','gclid','fbclid'}
def normalize(url):
    url = url.strip().replace('\\&','&')
    m = re.fullmatch(r'\[[^\]]*\]\((https?://.+)\)', url)
    if m: url = m.group(1)
    p = urlsplit(url)
    if p.scheme not in ('http','https') or not p.hostname or p.username or p.password:
        raise ValueError('Only public HTTP(S) URLs without credentials are accepted')
    pairs = [(k,v) for k,v in parse_qsl(p.query,keep_blank_values=True) if k.lower() not in TRACKING]
    host = p.hostname.lower()
    provider = 'jobkorea' if host == 'jobkorea.co.kr' or host.endswith('.jobkorea.co.kr') else 'saramin' if host == 'saramin.co.kr' or host.endswith('.saramin.co.kr') else 'generic'
    pid = None
    if provider == 'jobkorea':
        match = re.search(r'/Recruit/GI_Read/(\d+)',p.path,re.I)
        if match: pid = match.group(1)
    if provider == 'saramin': pid = dict(pairs).get('rec_idx')
    return {'original_url':url,'canonical_url':urlunsplit((p.scheme,p.netloc,p.path,urlencode(pairs),'')),'provider':provider,'posting_id':pid}

async def public_url(url):
    p = urlsplit(url)
    if p.scheme not in ('http','https') or p.username or p.password or p.port not in (None,80,443): return False
    try:
        addresses = await asyncio.get_running_loop().getaddrinfo(p.hostname,None)
        return bool(addresses) and all(ipaddress.ip_address(a[4][0]).is_global for a in addresses)
    except (OSError,ValueError): return False

EXTRACT = r'''() => {
 const roots = [...document.querySelectorAll('#giframe, #gib_frame, .recruit-detail, .user_content, .wrap_jv_cont, #job-detail, main, article')];
 const root = roots.find(e=>e.innerText?.trim().length>150) || document.body;
 const copy = root.cloneNode(true);
 copy.querySelectorAll('script,style,nav,header,footer,noscript').forEach(e=>e.remove());
 const structured=[];
 document.querySelectorAll('script[type="application/ld+json"]').forEach(e=>{try{structured.push(JSON.parse(e.textContent))}catch{}});
 return {title:document.title,text:copy.innerText||copy.textContent||'',structured,
 images:[...root.querySelectorAll('img')].filter(e=>e.naturalHeight>250||e.height>250).map(e=>({url:e.currentSrc||e.src,alt:e.alt,width:e.naturalWidth,height:e.naturalHeight})),
 pdf_links:[...root.querySelectorAll('a[href]')].filter(e=>/\.pdf(?:$|[?#])/i.test(e.href)).map(e=>e.href)};
}'''
GROUPS = {'duties':r'담당\s*업무|주요\s*업무|수행\s*업무|responsibilities|what you.ll do', 'requirements':r'지원\s*자격|자격\s*요건|필수\s*요건|requirements|qualifications', 'preferred':r'우대\s*사항|우대\s*조건|preferred|nice to have', 'experience':r'경력|신입|experience'}
def assess(text, unresolved=False):
    found = {k:bool(re.search(v,text,re.I)) for k,v in GROUPS.items()}
    # Keyword detection is a hint only; a model must verify content, identity, and full coverage.
    return {'status':'PARTIAL' if text.strip() else 'FAILED','section_hints':found,'requires_semantic_verification':True,'unresolved_visual_content':unresolved}

async def parse(url):
    info = normalize(url)
    from playwright.async_api import async_playwright
    attempts=[]; best=None
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(headless=True)
        try:
            for target in dict.fromkeys([info['original_url'],info['canonical_url']]):
                context=await browser.new_context(viewport={'width':1360,'height':900},accept_downloads=False)
                async def guard(route):
                    if await public_url(route.request.url): await route.continue_()
                    else: await route.abort()
                await context.route('**/*',guard)
                page=await context.new_page()
                try:
                    if not await public_url(target): raise ValueError('URL blocked or not publicly resolvable')
                    response=await page.goto(target,wait_until='domcontentloaded',timeout=30000)
                    if response and response.status>=400: raise ValueError('HTTP '+str(response.status))
                    # Bounded scroll triggers lazy content; never click apply/login controls.
                    for _ in range(5):
                        await page.evaluate('window.scrollBy(0,window.innerHeight)')
                        await page.wait_for_timeout(400)
                    frames=[]
                    for frame in page.frames[:20]:
                        try:
                            data=await frame.evaluate(EXTRACT)
                            data['url']=frame.url
                            frames.append(data)
                        except Exception: pass
                    texts=list(dict.fromkeys(f['text'].strip() for f in frames if f['text'].strip()))
                    text='\n\n'.join(texts)
                    images=[im for f in frames for im in f['images']]
                    pdfs=list(dict.fromkeys(u for f in frames for u in f['pdf_links']))
                    blocked=bool(re.search(r'access denied|captcha|로봇이 아닙니다|비정상적인 접근',text,re.I))
                    result={**info,'final_url':page.url,'title':await page.title(),'text':text,'frames':frames,'images':images,'pdf_links':pdfs,'completeness':assess(text,bool(images or pdfs)), 'blocked':blocked}
                    if blocked: result['completeness']['status']='FAILED'
                    attempts.append({'url':target,'status':result['completeness']['status']})
                    if best is None or (not blocked and len(text)>len(best['text'])): best=result
                except Exception as e: attempts.append({'url':target,'error':str(e)[:300]})
                finally: await context.close()
        finally: await browser.close()
    return {**(best or {**info,'text':'','completeness':assess('')}),'attempts':attempts}

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('url',nargs='?'); ap.add_argument('--mcp',action='store_true'); args=ap.parse_args()
    if args.mcp:
        from mcp.server.fastmcp import FastMCP
        server=FastMCP('recruitment-parser')
        @server.tool()
        async def parse_job_posting(url:str)->dict:
            """Render a public recruitment URL, extract DOM and frames; return source and coverage hints."""
            return await parse(url)
        server.run()
    else:
        try: print(json.dumps(asyncio.run(parse(args.url)),ensure_ascii=False))
        except Exception as e: print(json.dumps({'completeness':{'status':'FAILED'},'error':str(e)},ensure_ascii=False)); raise SystemExit(1)
