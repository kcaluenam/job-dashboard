import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import time

# --- CONFIGURATION ---
TARGETS = [
    {"name": "Datadog", "url": "https://boards.greenhouse.io/datadog", "type": "greenhouse"},
    {"name": "Anduril", "url": "https://boards.greenhouse.io/andurilindustries", "type": "greenhouse"},
    {"name": "Palantir", "url": "https://jobs.lever.co/palantir", "type": "lever"},
    {"name": "Linear", "url": "https://jobs.ashbyhq.com/linear", "type": "ashby"},
    {"name": "Rippling", "url": "https://jobs.ashbyhq.com/rippling", "type": "ashby"},
    {"name": "Vannevar Labs", "url": "https://jobs.ashbyhq.com/vannevarlabs", "type": "ashby"},
    {"name": "Scale AI", "url": "https://boards.greenhouse.io/scaleai", "type": "greenhouse"},
    {"name": "Anthropic", "url": "https://boards.greenhouse.io/anthropic", "type": "greenhouse"},
]

KEYWORDS = ["Solutions Engineer", "Sales Engineer", "Forward Deployed", "Deployment", "Technical Account"]
DB_FILE = "jobs_db.json"

# --- HELPER FUNCTIONS ---
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, 'w') as f:
        json.dump(db, f, indent=4)

def fetch_jobs(target):
    """Fetch jobs with proper error handling and rate limiting"""
    jobs = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    try:
        time.sleep(0.5)  # Be nice to the servers
        
        if target['type'] == 'greenhouse':
            resp = requests.get(target['url'], headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            for div in soup.find_all('div', class_='opening'):
                a = div.find('a')
                if a and a.get('href'):
                    href = a['href']
                    # Handle both relative and absolute URLs
                    if not href.startswith('http'):
                        href = "https://boards.greenhouse.io" + href
                    jobs.append((a.text.strip(), href))
        
        elif target['type'] == 'lever':
            resp = requests.get(target['url'], headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            for div in soup.find_all('div', class_='posting'):
                a = div.find('a', class_='posting-title')
                if a and a.get('href'):
                    h5 = a.find('h5')
                    if h5:
                        jobs.append((h5.text.strip(), a['href']))

        elif target['type'] == 'ashby':
            slug = target['url'].split('/')[-1]
            api_url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
            resp = requests.post(api_url, json={}, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            for job in data.get('jobs', []):
                if 'title' in job and 'jobUrl' in job:
                    jobs.append((job['title'], job['jobUrl']))
        
        print(f"✓ {target['name']}: Found {len(jobs)} total jobs")
        
    except requests.exceptions.Timeout:
        print(f"✗ {target['name']}: Timeout")
    except requests.exceptions.RequestException as e:
        print(f"✗ {target['name']}: Connection error")
    except Exception as e:
        print(f"✗ {target['name']}: Parse error - {type(e).__name__}")
    
    return jobs

# --- HTML GENERATOR ---
def generate_html(new_jobs, all_jobs):
    now = datetime.now()
    new_count = len(new_jobs)
    total_count = len(all_jobs)
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <title>🛏️ Job Feed</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: #f4f4f9;
            color: #1a1a1a;
            padding: env(safe-area-inset-top) 16px env(safe-area-inset-bottom) 16px;
            padding-top: max(20px, env(safe-area-inset-top));
            padding-bottom: max(20px, env(safe-area-inset-bottom));
            line-height: 1.5;
        }}
        
        header {{
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid #e5e5e5;
        }}
        
        h1 {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .stats {{
            display: flex;
            gap: 12px;
            margin-top: 12px;
            flex-wrap: wrap;
        }}
        
        .stat-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: white;
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }}
        
        .stat-badge.new {{
            background: #dcfce7;
            color: #166534;
        }}
        
        .timestamp {{
            font-size: 13px;
            color: #666;
            margin-top: 8px;
        }}
        
        .card {{
            background: white;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
            position: relative;
        }}
        
        .card:active {{
            transform: scale(0.98);
            box-shadow: 0 1px 2px rgba(0,0,0,0.06);
        }}
        
        .card-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }}
        
        .tag {{
            display: inline-block;
            background: #e0e7ff;
            color: #4338ca;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
        }}
        
        .new-badge {{
            background: #dcfce7;
            color: #166534;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }}
        
        .title {{
            font-size: 17px;
            font-weight: 600;
            display: block;
            text-decoration: none;
            color: #111;
            margin-bottom: 8px;
            line-height: 1.3;
        }}
        
        .title:hover {{
            color: #4338ca;
        }}
        
        .meta {{
            font-size: 12px;
            color: #888;
            display: flex;
            align-items: center;
            gap: 4px;
        }}
        
        .empty {{
            text-align: center;
            padding: 60px 20px;
            color: #888;
        }}
        
        .empty-icon {{
            font-size: 48px;
            margin-bottom: 16px;
            opacity: 0.5;
        }}
        
        .empty-text {{
            font-size: 16px;
            line-height: 1.6;
        }}
        
        /* Dark mode support */
        @media (prefers-color-scheme: dark) {{
            body {{
                background: #0a0a0a;
                color: #e5e5e5;
            }}
            
            header {{
                border-bottom-color: #2a2a2a;
            }}
            
            .card {{
                background: #1a1a1a;
                box-shadow: 0 1px 3px rgba(0,0,0,0.3);
            }}
            
            .stat-badge {{
                background: #1a1a1a;
                color: #e5e5e5;
            }}
            
            .stat-badge.new {{
                background: #166534;
                color: #dcfce7;
            }}
            
            .title {{
                color: #e5e5e5;
            }}
            
            .title:hover {{
                color: #818cf8;
            }}
            
            .tag {{
                background: #312e81;
                color: #c7d2fe;
            }}
            
            .new-badge {{
                background: #166534;
                color: #dcfce7;
            }}
            
            .meta {{
                color: #888;
            }}
            
            .timestamp {{
                color: #888;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <h1>🛏️ Bedtime Job Feed</h1>
        <div class="stats">
            <span class="stat-badge">📊 {total_count} total</span>
            {f'<span class="stat-badge new">✨ {new_count} fresh</span>' if new_count > 0 else ''}
        </div>
        <div class="timestamp">Updated {now.strftime("%b %d, %I:%M %p")}</div>
    </header>
    
    <main>
"""

    if not all_jobs:
        html_content += """
        <div class="empty">
            <div class="empty-icon">🔍</div>
            <div class="empty-text">
                No matching jobs found yet.<br>
                Check back tomorrow morning!
            </div>
        </div>
"""
    else:
        # Sort jobs: new first, then by date
        sorted_jobs = sorted(
            all_jobs.items(),
            key=lambda x: (x[0] not in new_jobs, x[1]['date']),
            reverse=True
        )

        for link, job in sorted_jobs:
            is_new = link in new_jobs
            new_tag = '<span class="new-badge">Fresh</span>' if is_new else ''
            
            html_content += f"""
        <div class="card">
            <div class="card-header">
                <span class="tag">{job['company']}</span>
                {new_tag}
            </div>
            <a href="{link}" target="_blank" rel="noopener" class="title">{job['title']}</a>
            <div class="meta">📅 Found {job['date']}</div>
        </div>
"""

    html_content += """
    </main>
</body>
</html>"""
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

# --- MAIN EXECUTION ---
def run():
    print("=" * 50)
    print(f"🚀 Starting job scan at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    db = load_db()
    new_links = []
    total_scanned = 0
    
    for target in TARGETS:
        found = fetch_jobs(target)
        total_scanned += len(found)
        
        for title, link in found:
            # Check if any keyword matches
            if any(k.lower() in title.lower() for k in KEYWORDS):
                if link not in db:
                    db[link] = {
                        "company": target['name'],
                        "title": title,
                        "date": datetime.now().strftime("%Y-%m-%d")
                    }
                    new_links.append(link)
                    print(f"  → NEW: {title}")
    
    save_db(db)
    generate_html(new_links, db)
    
    print("=" * 50)
    print(f"✅ Scan complete!")
    print(f"   Total jobs scanned: {total_scanned}")
    print(f"   Matching jobs in DB: {len(db)}")
    print(f"   Fresh jobs today: {len(new_links)}")
    print("=" * 50)

if __name__ == "__main__":
    run()
