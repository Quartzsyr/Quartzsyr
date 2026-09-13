#!/usr/bin/env python3
"""Build self-hosted profile cards from public GitHub data; standard library only."""
from __future__ import annotations
import datetime as dt
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import urllib.request
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
OWNER = os.getenv('GITHUB_REPOSITORY_OWNER', 'Quartzsyr')
TOKEN = os.getenv('GITHUB_TOKEN', '')
EXCLUDED = set(os.getenv('EXCLUDED_REPOS', 'Quartzsyr').split(','))

def fetch(url, api=True):
    headers = {'User-Agent': 'Quartz-profile', 'Accept': 'application/vnd.github+json' if api else 'text/html'}
    if api and TOKEN:
        headers['Authorization'] = 'Bearer ' + TOKEN
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
        raw = r.read().decode()
    return json.loads(raw) if api else raw

def repositories():
    rows, page = [], 1
    while True:
        batch = fetch(f'https://api.github.com/users/{OWNER}/repos?type=owner&per_page=100&page={page}')
        rows.extend(batch)
        if len(batch) < 100:
            return rows
        page += 1

class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.dates, self.counts, self.tip, self.buffer = {}, {}, None, ''
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('data-date') and a.get('id'):
            self.dates[a['id']] = a['data-date']
        if tag == 'tool-tip' and a.get('for', '').startswith('contribution-day-component-'):
            self.tip, self.buffer = a['for'], ''
    def handle_data(self, data):
        if self.tip:
            self.buffer += data
    def handle_endtag(self, tag):
        if tag == 'tool-tip' and self.tip:
            match = re.match(r'\s*(No|[\d,]+) contributions? on ', self.buffer)
            if match:
                self.counts[self.tip] = 0 if match[1] == 'No' else int(match[1].replace(',', ''))
            self.tip = None
    def days(self):
        if len(self.dates) < 350 or set(self.dates) - set(self.counts):
            raise ValueError('Incomplete contribution calendar; keeping existing cards')
        rows = sorted((date, self.counts[key]) for key, date in self.dates.items())
        dates = [dt.date.fromisoformat(d) for d, _ in rows]
        if any((b-a).days != 1 for a,b in zip(dates, dates[1:])):
            raise ValueError('Non-contiguous contribution calendar')
        return rows

def text(x,y,value,size=14,color='text',weight=400):
    return f'<text x="{x}" y="{y}" fill="var(--{color})" font-size="{size}" font-weight="{weight}">{html.escape(str(value))}</text>'

def card(theme, height, title, body):
    dark = theme == 'dark'
    colors = ['#0d1117','#30363d','#e6edf3','#8b949e','#161b22'] if dark else ['#ffffff','#d0d7de','#1f2328','#656d76','#f6f8fa']
    variables = ';'.join(f'--{k}:{v}' for k,v in zip(['bg','border','text','sub','track'],colors))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="{height}" viewBox="0 0 900 {height}" role="img" aria-label="{html.escape(title)}">
<title>{html.escape(title)}</title><style>svg{{{variables};font-family:Arial,sans-serif}}.reveal{{animation:reveal 1.4s ease-out both;transform-box:fill-box;transform-origin:left}}@keyframes reveal{{from{{transform:scaleX(.02);opacity:.2}}to{{transform:scaleX(1);opacity:1}}}}@media(prefers-reduced-motion:reduce){{.reveal{{animation:none}}}}</style>
<rect x=".5" y=".5" width="899" height="{height-1}" rx="16" fill="var(--bg)" stroke="var(--border)"/>
{text(28,34,title,13,'sub',700)}{body}</svg>'''

def overview(theme, profile, repos):
    own = [r for r in repos if not r['fork'] and not r['private']]
    values = [('ORIGINAL REPOS',len(own)),('STARS',sum(r['stargazers_count'] for r in own)),('FORKS',sum(r['forks_count'] for r in own)),('FOLLOWERS',profile['followers'])]
    body = ''.join(text(28+i*220,87,f'{v:,}',34,weight=700)+text(28+i*220,112,k,11,'sub') for i,(k,v) in enumerate(values))
    body += text(28,145,'Public, owned, non-fork repositories · Updated '+dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d UTC'),11,'sub')
    return card(theme,166,'GITHUB / OVERVIEW',body)

def languages(theme, totals):
    top = totals.most_common(6)
    if len(totals)>6:
        top.append(('Other',sum(totals.values())-sum(v for _,v in top)))
    palette=['#58a6ff','#a78bfa','#39d3bb','#f2cc60','#f78166','#db61a2','#8b949e']
    total=sum(totals.values())
    body=''
    x=28
    for i,(name,value) in enumerate(top):
        width=844*value/total
        body+=f'<rect class="reveal" x="{x:.2f}" y="56" width="{width:.2f}" height="12" fill="{palette[i]}"/>'
        x+=width
        xx=28+(i%4)*218; yy=101+(i//4)*29
        body+=f'<circle cx="{xx+4}" cy="{yy-4}" r="4" fill="{palette[i]}"/>'+text(xx+16,yy,f'{name} {value/total:.1%}',13)
    if not top:
        body+=text(28,95,'No language data available',14,'sub')
    body+=text(28,164,'Share of code bytes · Public originals · Archived repositories and this profile excluded',11,'sub')
    return card(theme,184,'CODE / LANGUAGES',body)

def activity(theme,days):
    values=[n for _,n in days]
    best=run=0
    for n in values:
        run=run+1 if n else 0
        best=max(best,run)
    labels=[('CONTRIBUTIONS',sum(values)),('ACTIVE DAYS',sum(n>0 for n in values)),('BEST STREAK',str(best)+' days'),('LAST 30 DAYS',sum(values[-30:]))]
    body=''.join(text(28+i*220,86,f'{v:,}' if isinstance(v,int) else v,30,weight=700)+text(28+i*220,110,k,11,'sub') for i,(k,v) in enumerate(labels))
    weeks=[sum(values[i:i+7]) for i in range(0,len(values),7)]
    peak=max(weeks) or 1
    for i,n in enumerate(weeks):
        h=max(2,n/peak*65)
        body+=f'<rect x="{28+i*844/len(weeks):.2f}" y="{202-h:.2f}" width="{844/len(weeks)-4:.2f}" height="{h:.2f}" rx="2" fill="'+('#39d3bb' if n else 'var(--track)')+f'"><title>{days[i*7][0]}: {n} contributions</title></rect>'
    body+=text(28,226,f'{days[0][0]} → {days[-1][0]} · Weekly contributions · Best streak within this period',11,'sub')
    return card(theme,247,'ACTIVITY / PAST YEAR',body)

def main():
    # Fetch and validate everything before replacing any existing assets.
    profile=fetch(f'https://api.github.com/users/{OWNER}')
    repos=repositories()
    totals=Counter()
    for r in repos:
        if not r['fork'] and not r['private'] and not r['archived'] and r['name'] not in EXCLUDED:
            totals.update(fetch(r['languages_url']))
    parser=Calendar()
    parser.feed(fetch(f'https://github.com/users/{OWNER}/contributions',api=False))
    days=parser.days()
    assets={}
    for theme in ['dark','light']:
        assets[f'stats-{theme}.svg']=overview(theme,profile,repos)
        assets[f'languages-{theme}.svg']=languages(theme,totals)
        assets[f'activity-{theme}.svg']=activity(theme,days)
    ASSETS.mkdir(exist_ok=True)
    for name,body in assets.items():
        (ASSETS/name).write_text(body)
    print(f'Generated {len(assets)} cards from {len(repos)} public repositories and {len(days)} contribution days.')
if __name__=='__main__':
    main()
