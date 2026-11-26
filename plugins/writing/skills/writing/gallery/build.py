"""Build gallery.html, the reference page of the house style components.

Run: python3 build.py   (writes gallery.html next to this file)

The gallery is a house style page itself: it uses the head, the CSS and the script of
starter.html. Each example is the starter element with that data-g id. Each full rule is the
matching ### section of artifacts.md. gallery.json holds names, areas, purposes, variants,
"use when" lists and parts. Gallery-only classes start with "gal-", so they cannot clash with
component classes.
"""
import html, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
starter = open(os.path.join(SKILL, 'starter.html')).read()
rules_md = open(os.path.join(SKILL, 'artifacts.md')).read()
spec = json.load(open(os.path.join(HERE, 'gallery.json')))
esc = html.escape


def sample(gid):
    """Return the outer HTML of the starter element with data-g="gid"."""
    at = starter.index(f'data-g="{gid}"')
    start = starter.rindex('<', 0, at)
    tag = re.match(r'<(\w+)', starter[start:]).group(1)
    depth = 0
    for m in re.compile(rf'<(/?){tag}\b[^>]*>').finditer(starter, start):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            out = starter[start:m.end()]
            if gid == 'tabs':  # the example must not drive the page tabs; show its first tab open
                out = out.replace(' id="tabs"', '').replace('<button role="tab"', '<button role="tab" aria-selected="true"', 1)
            return out
    raise ValueError(gid)


def inline(t):
    t = esc(t)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    return re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', t)


def rule(heading):
    """The ### section of artifacts.md with this name, as HTML in the house style."""
    if not heading:
        return '<p class="gal-none">No rule yet.</p>'
    m = re.search(rf'^#{{2,3}} {re.escape(heading)}\n(.*?)(?=^#{{2,3}} |\Z)', rules_md, re.S | re.M)
    if not m:
        return f'<p class="gal-none">No section "{esc(heading)}" in artifacts.md.</p>'
    out, rows, items = [], [], []
    def flush():
        if rows:
            out.append('<div class="tw"><table><thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in rows[0]) + '</tr></thead><tbody>'
                       + ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>' for r in rows[2:]) + '</tbody></table></div>')
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
            flush(); out.append(f'<p>{inline(line)}</p>')
        else:
            flush()
    flush()
    return f'<p class="gal-src">artifacts.md, section "{esc(heading)}"</p>' + ''.join(out)


MARK = {'approved': '<i class="mk done">✓</i>', 'draft': '<i class="mk you">?</i>'}


def component(c):
    ex = sample(c['g']) if c.get('g') else c.get('html', '')
    src = f'starter.html, data-g="{c["g"]}"' if c.get('g') else 'gallery.json'
    vars_ = ''.join(f'<div class="gal-var"><div class="gal-lbl">{esc(l)}</div><div class="gal-ex">{h}</div></div>' for l, h in c.get('variants', []))
    use = ''.join(f'<li>{esc(x)}</li>' for x in c.get('use', []))
    avoid = ''.join(f'<li>{esc(x)}</li>' for x in c.get('avoid', []))
    parts = ''.join(f'<tr><td>{esc(p[0])}</td><td><code>{esc(p[1])}</code></td><td>{esc(p[2])}</td></tr>' if p[1] else f'<tr><td>{esc(p[0])}</td><td></td><td>{esc(p[2])}</td></tr>' for p in c.get('parts', []))
    return f'''<section class="gal-c" id="g-{c['id']}">
<div class="gal-h"><h2>{esc(c['name'])}</h2>{MARK.get(c.get('status'), '')}</div>
<p class="gal-p">{esc(c.get('purpose', ''))}</p>
<p class="gal-src">{esc(src)}</p>
<div class="gal-lbl">Example</div>
<div class="gal-ex">{ex}</div>
{f'<div class="gal-lbl">Variants</div><div class="gal-vars">{vars_}</div>' if vars_ else ''}
<div class="gal-use"><div class="card"><h3>Use when</h3><ul>{use}</ul></div><div class="card"><h3>Do not use when</h3><ul>{avoid}</ul></div></div>
<div class="gal-lbl">Parts</div>
<div class="tw"><table><thead><tr><th>Part</th><th>Class</th><th>Value</th></tr></thead><tbody>{parts}</tbody></table></div>
<div class="fl">
<details><summary><span class="tt"><b>Code</b><small>HTML to copy</small></span></summary><div class="body"><div class="cb"><div class="bar-top"><span>{esc(src)}</span><span>HTML</span></div><div class="scroll"><pre>{esc(ex)}</pre></div></div></div></details>
<details><summary><span class="tt"><b>Full rule</b><small>From artifacts.md</small></span></summary><div class="body gal-rule">{rule(c.get('rule'))}</div></details>
</div>
</section>'''


def area(a, name):
    comps = [c for c in spec['components'] if c['area'] == a]
    if a not in spec.get('built', []):
        return f'<section class="tab" data-p="{a}" hidden><div class="note"><b>Not built yet.</b> This tab follows when the format of the Structures tab is approved. {len(comps)} components.</div></section>'
    rows = ''.join(f'<tr><td><a href="#g-{c["id"]}" class="gal-jump">{esc(c["name"])}</a></td><td>{esc(c.get("use", [""])[0])}</td><td>{MARK.get(c.get("status"), "")}</td></tr>' for c in comps)
    return f'''<section class="tab" data-p="{a}" hidden>
<div class="tw gal-index"><table><thead><tr><th>Component</th><th>Use for</th><th>State</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="gal-src">{MARK['approved']} approved · {MARK['draft']} rule is a draft</p>
{''.join(component(c) for c in comps)}
</section>'''


style = re.search(r'<style>(.*?)</style>', starter, re.S).group(1)
script = re.search(r'<script>(.*?)</script>', starter, re.S).group(1)
fonts = re.search(r'<link rel="stylesheet"[^>]+>', starter).group(0)
first = spec.get('built', [spec['areas'][0][0]])[0]
areas = sorted(spec['areas'], key=lambda x: x[0] != first)
page = f'''<title>{esc(spec['title'])}</title>
<meta name="claude:viewport-fit-sides" content="cover">
{fonts}
<style>
/* Built by gallery/build.py from starter.html, artifacts.md and gallery.json. Do not edit by hand. */
{style}
/* gallery-only classes */
.gal-c{{display:flex;flex-direction:column;gap:12px;padding-top:28px;margin-top:12px;border-top:1px solid var(--line)}}
.gal-h{{display:flex;align-items:center;gap:10px}}
.gal-h h2{{font-size:22px}}
.gal-p{{font-size:16px;max-width:70ch}}
.gal-src{{font:12px var(--mono);color:var(--muted)}}
.gal-lbl{{font:600 11px var(--mono);letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-top:4px}}
.gal-ex{{display:flex;flex-direction:column;gap:10px}}
.gal-vars{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr));gap:16px}}
.gal-var{{display:flex;flex-direction:column;gap:6px}}
.gal-use{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));gap:12px}}
.gal-use .card ul{{font-size:14px}}
.gal-rule{{font-size:14px}}
.gal-rule ul{{gap:4px}}
.gal-none{{color:var(--muted);font-style:italic}}
.gal-jump{{font-weight:600;text-decoration:none}}
</style>
<div class="wrap">
  <header>
    <span class="eyebrow">Writing skill · House style</span>
    <h1>{esc(spec['title'])}</h1>
    <p class="lead">{esc(spec.get('lead', ''))}</p>
  </header>
  <nav class="tabs" id="tabs" role="tablist">
    {''.join(f'<button role="tab" data-t="{a}">{esc(n)}</button>' for a, n in areas)}
  </nav>
  {''.join(area(a, n) for a, n in areas)}
</div>
<script>
{script}
</script>
'''
open(os.path.join(HERE, 'gallery.html'), 'w').write(page)
print('gallery.html:', ', '.join(spec.get('built', [])), 'built,', len(page) // 1024, 'KB')
