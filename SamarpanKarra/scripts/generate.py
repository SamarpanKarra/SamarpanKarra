"""Builds assets/contrib-heatmap.svg and assets/stats.svg from your GitHub contribution calendar.
Run by the daily workflow. Locally (no token) it renders demo data so you can preview the look."""
import os, json, random, datetime as dt, urllib.request

BLUE, NAVY, TINT = "#0018f9", "#0f1340", "#8fa0ff"
CELL = ["#1b2070", "#2a3bc0", BLUE, "#5a70ff", TINT]   # 0 .. 4 (empty -> busiest)
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
USER, TOKEN = os.getenv("GH_USER"), os.getenv("GH_TOKEN")

def fetch():
    q = """query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{
      totalContributions weeks{contributionDays{date contributionCount}}}}}}"""
    req = urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query": q, "variables": {"u": USER}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"})
    cal = json.load(urllib.request.urlopen(req))["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return [[(d["date"], d["contributionCount"]) for d in w["contributionDays"]] for w in cal["weeks"]]

def demo():
    random.seed(4); end = dt.date.today(); start = end - dt.timedelta(days=364)
    start -= dt.timedelta(days=(start.weekday() + 1) % 7)       # align to Sunday
    weeks, d = [], start
    while d <= end:
        wk = []
        for _ in range(7):
            n = max(0, int(random.gauss(2.2, 3))) if random.random() > .35 else 0
            wk.append((d.isoformat(), n)); d += dt.timedelta(days=1)
        weeks.append(wk)
    return weeks

weeks = fetch() if (USER and TOKEN) else demo()
today = dt.date.today().isoformat()
days = [x for w in weeks for x in w if x[0] <= today]
total = sum(n for _, n in days)
best = run = 0
for _, n in days:
    run = run + 1 if n else 0; best = max(best, run)
cur = 0
for i, (_, n) in enumerate(reversed(days)):
    if n: cur += 1
    elif i == 0: continue          # today may not have a contribution yet
    else: break
mx = max((n for _, n in days), default=1) or 1
lvl = lambda n: 0 if n == 0 else min(4, 1 + int(3 * (n - 1) / max(mx - 1, 1) + .0001))

# ---------- heatmap ----------
S, G, X0, Y0 = 11, 3, 44, 62
W = X0 + len(weeks) * (S + G) + 24; H = Y0 + 7 * (S + G) + 46
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
     f'<rect width="{W}" height="{H}" rx="12" fill="{NAVY}"/>',
     '<circle cx="22" cy="22" r="5" fill="#ff5f56"/><circle cx="40" cy="22" r="5" fill="#ffbd2e"/><circle cx="58" cy="22" r="5" fill="#27c93f"/>',
     f'<text x="{W//2}" y="26" fill="{TINT}" font-size="12" text-anchor="middle">contributions: {total} in the last year</text>']
last_m = None
for i, wk in enumerate(weeks):
    m = dt.date.fromisoformat(wk[0][0]).strftime("%b")
    if m != last_m:
        o.append(f'<text x="{X0 + i*(S+G)}" y="{Y0-8}" fill="{TINT}" font-size="10">{m}</text>'); last_m = m
    for j, (d, n) in enumerate(wk):
        if d > today: continue
        o.append(f'<rect x="{X0 + i*(S+G)}" y="{Y0 + j*(S+G)}" width="{S}" height="{S}" rx="2" fill="{CELL[lvl(n)]}"><title>{d}: {n}</title></rect>')
for j, lab in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
    o.append(f'<text x="10" y="{Y0 + j*(S+G) + 9}" fill="{TINT}" font-size="9">{lab}</text>')
ly = H - 16; lx = W - 24 - 5 * (S + 4) - 70
o.append(f'<text x="{lx}" y="{ly+9}" fill="{TINT}" font-size="10">less</text>')
for k, c in enumerate(CELL):
    o.append(f'<rect x="{lx + 30 + k*(S+4)}" y="{ly}" width="{S}" height="{S}" rx="2" fill="{c}"/>')
o.append(f'<text x="{lx + 34 + 5*(S+4)}" y="{ly+9}" fill="{TINT}" font-size="10">more</text></svg>')
open("assets/contrib-heatmap.svg", "w").write("\n".join(o))

# ---------- stats ----------
def stat(y, big, label):
    return (f'<text x="36" y="{y}" fill="#fff" font-size="40" font-weight="700">{big}</text>'
            f'<text x="36" y="{y+22}" fill="{TINT}" font-size="13">{label}</text>')
s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="420" height="320" viewBox="0 0 420 320" font-family="{FONT}">',
     f'<rect width="420" height="320" rx="12" fill="{NAVY}"/>',
     '<circle cx="22" cy="22" r="5" fill="#ff5f56"/><circle cx="40" cy="22" r="5" fill="#ffbd2e"/><circle cx="58" cy="22" r="5" fill="#27c93f"/>',
     f'<text x="210" y="26" fill="{TINT}" font-size="12" text-anchor="middle">./stats.sh</text>',
     f'<rect x="20" y="52" width="4" height="236" rx="2" fill="{BLUE}"/>',
     stat(98, total, "contributions · last 12 months"),
     stat(180, f"{cur} days", "current streak"),
     stat(262, f"{best} days", "longest streak"), '</svg>']
open("assets/stats.svg", "w").write("\n".join(s))
print("ok", total, cur, best, "(live)" if (USER and TOKEN) else "(demo)")
