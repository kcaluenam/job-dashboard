import requests
import re
import json
import os
from datetime import datetime
import time

# --- CONFIGURATION ---
TARGETS = [
    {"name": "Datadog", "url": "https://boards.greenhouse.io/datadog"},
    {"name": "Anduril", "url": "https://boards.greenhouse.io/andurilindustries"},
    {"name": "Palantir", "url": "https://jobs.lever.co/palantir"},
    {"name": "Linear", "url": "https://jobs.ashbyhq.com/linear"},
    {"name": "Rippling", "url": "https://jobs.ashbyhq.com/rippling"},
    {"name": "Vannevar Labs", "url": "https://jobs.ashbyhq.com/vannevarlabs"},
    {"name": "Hadrian", "url": "https://jobs.ashbyhq.com/hadrian"},
    {"name": "MongoDB", "url": "https://boards.greenhouse.io/mongodb"},
]

# Keywords to match (Case insensitive)
KEYWORDS = [
    "Solutions Engineer", "Sales Engineer", "Forward Deployed", 
    "Deployment", "Implementation", "Solutions Consultant",
    "Technical Success", "Partner Engineer"
]

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

def fetch_jobs_via_jina(target):
    jobs = []
    print(f"Scanning {target['name']} via Jina...")
    
    # The Magic Trick: Prepend r.jina.ai to the URL
    jina_url = f"https://r.jina.ai/{target['url']}"
    
    try:
        # We assume standard Markdown return: [Job Title](URL)
        response = requests.get(jina_url, timeout=30)
        
        if response.status_code == 200:
            content = response.text
            
            # Regex to find all markdown links: [Title](URL)
            # This captures the Title in group 1 and URL in group 2
            links = re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', content)
            
            for title, link in links:
                # Clean up title (remove extra whitespace/newlines)
                clean_title = title.replace('\n', ' ').strip()
                
                # Filter 1: Check if it matches our Keywords
                if any(k.lower() in clean_title.lower() for k in KEYWORDS):
                    # Filter 2: Ensure it's actually a job link (sanity check)
                    # Greenhouse/Lever links usually contain the company name or 'jobs'
                    if target['name'].lower() in link.lower() or 'boards' in link or 'jobs' in link:
                        jobs.append((clean_title, link))
        else:
            print(f"  ❌ Jina Error {response.status_code}")
            
    except Exception as e:
        print(f"  ⚠️ Error: {e}")

    print(f"  -> Found {len(jobs)} matches")
    return jobs

# --- HTML GENERATOR ---
def generate_html(new_jobs, all_jobs):
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Bedtime Job Feed</title>
        <style>
            body {{ font-family: -apple-system, system-ui, sans-serif; background: #f0f2f5; padding: 20px; color: #1c1e21; }}
            .card {{ background: white; border-radius: 12px; padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }}
            .tag {{ background: #e7f3ff; color: #1877f2; padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: bold; }}
            .title {{ font-size: 16px; font-weight: 600; display: block; margin-top: 8px; text-decoration: none; color: #1c1e21; }}
            .new {{ background: #e4f7eb; color: #09a244; padding: 2px 6px; border-radius: 4px; font-size: 10px; margin-left: 8px; }}
            .meta {{ color: #65676b; font-size: 12px; margin-top: 5px; }}
        </style>
    </head>
    <body>
        <h1>🛏️ Bedtime Feed (AI Powered)</h1>
        <div style="margin-bottom: 20px; color: #666; font-size: 13px;">Updated: {datetime.now().strftime("%I:%M %p")}</div>
        {'<div style="text-align:center; margin-top:50px; color:#888;">No new jobs.</div>' if not all_jobs else ''}
    """
    sorted_jobs = sorted(all_jobs.items(), key=lambda x: x[1]['date'], reverse=True)
    for link, job in sorted_jobs:
        is_new = link in new_jobs
        new_badge = '<span class="new">FRESH</span>' if is_new else ''
        html_content += f"""
        <div class="card">
            <div><span class="tag">{job['company']}</span>{new_badge}</div>
            <a href="{link}" target="_blank" class="title">{job['title']}</a>
            <div class="meta">Found: {job['date']}</div>
        </div>
        """
    html_content += "</body></html>"
    with open("index.html", "w") as f: f.write(html_content)

# --- RUN ---
def run():
    db = load_db()
    new_links = []
    
    for target in TARGETS:
        found_jobs = fetch_jobs_via_jina(target)
        for title, link in found_jobs:
            if link not in db:
                print(f"  ★ NEW: {title}")
                db[link] = { "company": target['name'], "title": title, "date": datetime.now().strftime("%Y-%m-%d") }
                new_links.append(link)
        time.sleep(2) # Be polite to Jina's free tier
    
    save_db(db)
    generate_html(new_links, db)

if __name__ == "__main__":
    run()
