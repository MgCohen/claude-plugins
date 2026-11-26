"""Build gallery.html from starter.html, artifacts.md and gallery.json.

Run: python3 build.py   (writes gallery.html next to this file)

The gallery shows each component from the real starter code. Samples come from the elements
with a data-g attribute in starter.html. The draft rules come from the ### sections of
artifacts.md. Only names, areas, variants and parts live in gallery.json.
"""
import html, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
starter = open(os.path.join(SKILL, 'starter.html')).read()
rules_md = open(os.path.join(SKILL, 'artifacts.md')).read()
spec = json.load(open(os.path.join(HERE, 'gallery.json')))


def sample(gid):
    """Return the outer HTML of the starter element with data-g="gid"."""
    at = starter.index(f'data-g="{gid}"')
    start = starter.rindex('<', 0, at)
    tag = re.match(r'<(\w+)', starter[start:]).group(1)
    depth, i = 0, start
    pat = re.compile(rf'<(/?){tag}\b[^>]*>')
    for m in pat.finditer(starter, start):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            out = starter[start:m.end()]
            if gid == 'tabs':  # the tab sample must not drive the gallery; show its first tab open
                out = out.replace(' id="tabs"', '').replace('<button role="tab"', '<button role="tab" aria-selected="true"', 1)
            return out
    raise ValueError(gid)


def scope_css(css, root='.gx'):
    """Put each starter rule under the sample container, so it cannot style the gallery."""
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    out, i = [], 0
    while i < len(css):
        j = css.find('{', i)
        if j < 0:
            break
        head = css[i:j].strip()
        if head.startswith('@media'):
            depth, k = 1, j + 1
            while depth:
                depth += {'{': 1, '}': -1}.get(css[k], 0)
                k += 1
            out.append(head + '{' + scope_css(css[j + 1:k - 1], root) + '}')
            i = k
            continue
        k = css.find('}', j)
        body = css[j + 1:k]
        sels = []
        for sel in head.split(','):
            sel = re.sub(r'/\*.*?\*/', '', sel, flags=re.S).strip()
            if not sel or sel == 'body::before':
                continue
            if sel in (':root', 'html', 'body'):
                sels.append(root)
            elif sel.startswith(':root'):
                sels.append(sel + ' ' + root)
            else:
                sels.append(root + ' ' + sel)
        if sels:
            out.append(','.join(sels) + '{' + body + '}')
        i = k + 1
    return '\n'.join(out)


def md_section(heading):
    """Return the markdown of the ### section with this name, as simple HTML."""
    if not heading:
        return '<p class="none">No draft rule yet.</p>'
    m = re.search(rf'^#{{2,3}} {re.escape(heading)}\n(.*?)(?=^#{{2,3}} |\Z)', rules_md, re.S | re.M)
    if not m:
        return f'<p class="none">No section "{html.escape(heading)}" in artifacts.md.</p>'
    def inline(t):
        t = html.escape(t)
        t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
        return re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', t)
    out, rows, items = [], [], []
    def flush():
        if rows:
            head, body = rows[0], [r for r in rows[2:]]
            out.append('<table><thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in head) + '</tr></thead><tbody>'
                       + ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>' for r in body) + '</tbody></table>')
            rows.clear()
        if items:
            out.append('<ul>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + '</ul>')
            items.clear()
    for line in m.group(1).splitlines():
        if line.startswith('|'):
            if items: flush()
            rows.append([c.strip() for c in line.strip().strip('|').split('|')])
        elif line.startswith('- '):
            if rows: flush()
            items.append(line[2:])
        elif line.startswith('  ') and items:
            items[-1] += ' ' + line.strip()
        elif line.strip():
            flush()
            out.append(f'<p>{inline(line)}</p>')
        else:
            flush()
    flush()
    return f'<div class="src">From artifacts.md, section "{html.escape(heading)}"</div>' + ''.join(out)


style = re.search(r'<style>(.*?)</style>', starter, re.S).group(1)
script = re.search(r'<script>(.*?)</script>', starter, re.S).group(1)
fonts = re.search(r'<link rel="stylesheet"[^>]+>', starter).group(0)

cards = []
for c in spec['components']:
    main = sample(c['g']) if c.get('g') else c['html']
    variants = ''.join(f'<div class="var"><div class="cap">{html.escape(lbl)}</div><div class="frame"><div class="gx">{h}</div></div></div>'
                       for lbl, h in c.get('variants', []))
    parts = ''.join(f'<tr><td>{html.escape(a)}</td><td>{html.escape(b)}</td></tr>' for a, b in c.get('parts', []))
    src = f'starter.html, data-g="{c["g"]}"' if c.get('g') else 'gallery.json'
    cards.append(f'''<details class="comp" id="c-{c['id']}" data-area="{c['area']}">
<summary><span class="head"><span class="arrow"></span><span class="name">{html.escape(c['name'])}<small>{html.escape(c['what'])}</small></span></span><span class="ans" data-id="{c['id']}"><button type="button" data-v="Keep" aria-pressed="false">Keep</button><button type="button" data-v="Change" aria-pressed="false">Change</button></span></summary>
<div class="body">
<div class="lbl">1 · Component <span class="src">{html.escape(src)}</span></div>
<div class="frame"><div class="gx">{main}</div></div>
{f'<div class="lbl">2 · Variants</div><div class="vars">{variants}</div>' if variants else '<div class="lbl">2 · Variants</div><p class="none">One form only.</p>'}
<div class="lbl">3 · Details</div><table class="parts"><tbody>{parts}</tbody></table>
<div class="lbl">4 · Draft rule</div><div class="rule">{md_section(c.get('rule'))}</div>
<div class="lbl">5 · Note</div><textarea data-id="{c['id']}" placeholder="What to change"></textarea><span class="saved" data-saved="{c['id']}"></span>
</div></details>''')

tabs = ''.join(f'<button type="button" data-a="{a}">{html.escape(n)} <em>{sum(1 for c in spec["components"] if c["area"] == a)}</em></button>' for a, n in spec['areas'])

page = f'''<title>{html.escape(spec['title'])}</title>
<meta name="claude:viewport-fit-sides" content="cover">
{fonts}
<style>
/* Gallery frame: plain system font, so that only the samples carry the house style.
   Built by gallery/build.py from starter.html, artifacts.md and gallery.json. Do not edit by hand. */
:root{{color-scheme:light dark;--g-bg:light-dark(#ffffff,#121212);--g-ink:light-dark(#111111,#eeeeee);--g-soft:light-dark(#666666,#a0a0a0);--g-rule:light-dark(#dddddd,#333333)}}
:root[data-theme=light]{{color-scheme:light}}:root[data-theme=dark]{{color-scheme:dark}}
*{{box-sizing:border-box;min-width:0}}
[hidden]{{display:none!important}}
body{{background:var(--g-bg);color:var(--g-ink);font:16px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;margin:0;overflow-x:clip}}
.gw{{max-width:860px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:24px 64px}}
.gw>h1{{font-size:26px;margin:0 0 6px}}
.intro{{margin:0 0 10px;max-width:68ch}}
.gtabs{{display:flex;flex-wrap:wrap;gap:6px;margin:14px 0;padding-bottom:12px;border-bottom:1px solid var(--g-rule)}}
.gtabs button{{font:500 14px system-ui,sans-serif;padding:6px 12px;border:1px solid var(--g-rule);border-radius:99px;background:var(--g-bg);color:var(--g-ink);cursor:pointer}}
.gtabs button em{{font-style:normal;color:var(--g-soft);font-size:12px}}
.gtabs button[aria-selected=true]{{background:var(--g-ink);color:var(--g-bg);border-color:var(--g-ink)}}
.gtabs button[aria-selected=true] em{{color:var(--g-bg)}}
details.comp{{border:1px solid var(--g-rule);border-radius:8px;margin-bottom:10px}}
details.comp>summary{{list-style:none;cursor:pointer;padding:10px 12px;display:flex;flex-wrap:wrap;align-items:center;gap:8px 12px}}
details.comp>summary::-webkit-details-marker{{display:none}}
.head{{flex:1 1 240px;display:flex;gap:8px;align-items:baseline}}
.arrow::before{{content:"\\25B8";color:var(--g-soft)}}
details.comp[open] .arrow::before{{content:"\\25BE"}}
.name{{font-weight:600}}
.name small{{display:block;font-weight:400;color:var(--g-soft);font-size:14px}}
.ans{{display:flex;gap:6px}}
.ans button{{font:500 14px system-ui,sans-serif;min-height:34px;padding:4px 12px;border-radius:6px;border:1px solid var(--g-rule);background:var(--g-bg);color:var(--g-ink);cursor:pointer}}
.ans button[aria-pressed=true]{{background:var(--g-ink);color:var(--g-bg);border-color:var(--g-ink)}}
.body{{padding:4px 12px 14px;border-top:1px solid var(--g-rule)}}
.lbl{{font-size:13px;font-weight:700;color:var(--g-soft);margin:14px 0 6px;display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap}}
.lbl .src,.rule .src{{font-weight:400;font-family:ui-monospace,monospace;font-size:11.5px}}
.frame{{border:2px dashed var(--g-soft);border-radius:6px;overflow:hidden}}
.vars{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,240px),1fr));gap:10px}}
.cap{{font-size:13px;font-weight:600;margin-bottom:4px}}
table.parts{{border-collapse:collapse;width:100%;font-size:14px}}
table.parts td{{border-top:1px solid var(--g-rule);padding:5px 8px;vertical-align:top}}
table.parts td:first-child{{color:var(--g-soft);width:34%}}
.rule{{font-size:14px;border-left:3px solid var(--g-rule);padding:2px 0 2px 12px}}
.rule p,.rule ul{{margin:4px 0}}
.rule table{{border-collapse:collapse;font-size:13px;margin:6px 0;width:100%}}
.rule th,.rule td{{border-top:1px solid var(--g-rule);padding:4px 6px;text-align:left;vertical-align:top}}
.rule code{{font-size:12px}}
.none{{color:var(--g-soft);font-style:italic;margin:0}}
textarea{{width:100%;min-height:50px;font:15px system-ui,sans-serif;padding:8px;border:1px solid var(--g-rule);border-radius:6px;background:var(--g-bg);color:var(--g-ink)}}
.saved{{font-size:13px;color:var(--g-soft)}}
.warn{{border:1px solid var(--g-rule);padding:8px 12px;border-radius:6px;margin-bottom:12px}}
/* the starter CSS, scoped to .gx */
{scope_css(style)}
.gx{{padding:16px;display:flex;flex-direction:column;gap:12px}}
.gx .swatches{{display:grid;grid-template-columns:repeat(auto-fit,minmax(90px,1fr));gap:8px}}
.gx .swatches div{{border:1px solid var(--line);border-radius:8px;overflow:hidden;background:var(--surface);font:11px var(--mono)}}
.gx .swatches i{{display:block;height:34px}}
.gx .swatches span{{display:block;padding:4px 8px}}
</style>
<div class="gw">
<h1>{html.escape(spec['title'])}</h1>
<p class="intro">Each approved component, taken from the real starter page. Open a component to see it, its variants, its parts and its draft rule. Mark it Keep or Change. <span id="count"></span></p>
<div class="warn" id="nosave" hidden>Answers do not save in this view. Send them in the chat.</div>
<nav class="gtabs" id="gtabs">{tabs}</nav>
{''.join(cards)}
</div>
<script>
{{
/* gallery: area tabs */
const gt=document.getElementById("gtabs");
const area=a=>{{if(!gt.querySelector(`[data-a="${{a}}"]`))a=gt.querySelector("button").dataset.a;gt.querySelectorAll("button").forEach(b=>b.setAttribute("aria-selected",b.dataset.a===a?"true":"false"));document.querySelectorAll("details.comp").forEach(d=>d.hidden=d.dataset.area!==a);}};
gt.addEventListener("click",e=>{{const b=e.target.closest("button");if(b)location.hash="a-"+b.dataset.a;}});
window.addEventListener("hashchange",()=>area(location.hash.slice(3)));
area(location.hash.slice(3));
/* answers: Keep or Change, and a note, saved in the page database */
const state={{}};const ids=[...document.querySelectorAll(".ans")].map(a=>a.dataset.id);
const paint=()=>{{document.querySelectorAll(".ans").forEach(a=>{{const v=state[a.dataset.id]?.choice;a.querySelectorAll("button").forEach(b=>b.setAttribute("aria-pressed",b.dataset.v===v?"true":"false"));}});document.querySelectorAll("textarea").forEach(t=>{{const n=state[t.dataset.id]?.note;if(document.activeElement!==t&&n!==undefined)t.value=n;}});document.getElementById("count").textContent=`${{ids.filter(i=>state[i]?.choice).length}} of ${{ids.length}} answered.`;}};
let db=null;
const save=id=>{{if(!db)return;const el=document.querySelector(`[data-saved="${{id}}"]`);db.collection("gallery").doc(id).set({{choice:state[id]?.choice||"",note:state[id]?.note||""}}).then(()=>el.textContent="Saved.").catch(()=>el.textContent="Not saved. Send it in the chat.");}};
document.addEventListener("click",e=>{{const b=e.target.closest(".ans button");if(!b)return;e.preventDefault();e.stopPropagation();const id=b.parentElement.dataset.id;state[id]={{...state[id],choice:state[id]?.choice===b.dataset.v?"":b.dataset.v}};paint();save(id);}},true);
document.querySelectorAll("textarea").forEach(t=>t.addEventListener("change",()=>{{const id=t.dataset.id;state[id]={{...state[id],note:t.value}};save(id);}}));
paint();
(async()=>{{try{{db=await window.claude?.use?.("db");}}catch(e){{db=null}}if(!db){{document.getElementById("nosave").hidden=false;return;}}db.collection("gallery").onSnapshot(s=>{{s.docs.forEach(d=>state[d.id]=d.data()||{{}});paint();}},()=>document.getElementById("nosave").hidden=false);}})();
}}
</script>
<script>
{script}
</script>
'''
open(os.path.join(HERE, 'gallery.html'), 'w').write(page)
print('gallery.html:', len(spec['components']), 'components,', len(page) // 1024, 'KB')
