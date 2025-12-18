import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

# --- CONFIGURATION ---
TARGETS = [
    # Tier 1: Dev Tools (Greenhouse)
    {"name": "Datadog", "url": "https://boards.greenhouse.io/datadog", "type": "greenhouse"},
    {"name": "MongoDB", "url": "https://boards.greenhouse.io/mongodb", "type": "greenhouse"},
    {"name": "Postman", "url": "https://boards.greenhouse.io/postman", "type": "greenhouse"},
    
    # Tier 2: Defense / Hard Tech
    {"name": "Anduril", "url": "https://boards.greenhouse.io/andurilindustries", "type": "greenhouse"},
    {"name": "Palantir", "url": "https://jobs.lever.co/palantir", "type": "lever"},
    {"name": "Vannevar Labs", "url": "https://jobs.ashbyhq.com/vannevarlabs", "type": "ashby"},
    {"name": "Hadrian", "url": "https://jobs.ashbyhq.com/hadrian", "type": "ashby"},
    
    # Tier 3: Startups (Ashby)
    {"name": "Linear", "url": "https://jobs.ashbyhq.com/linear", "type": "ashby"},
    {"name": "Rippling", "url": "https://jobs.ashbyhq.com/rippling", "type": "ashby"},
]

# Keywords to search for
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

def fetch_jobs(target):
    jobs = []
    # THIS IS THE SECRET SAUCE: Disguise as a Mac user
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5"
    }
    
    print(f"Scanning {target['name']}...") # Debug print
    
    try:
        if target['type'] == 'greenhouse':
            response = requests.get(target['url'], headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                for div in soup.find_all('div', class_='opening'):
                    a = div.find('a')
                    if a: 
                        link = a['href']
                        if not link.startswith('http'): link = "https://boards.greenhouse.io" + link
                        jobs.append((a.text.strip(), link))
            else:
                print(f"  ❌ Blocked by Greenhouse (Status {response.status_code})")

        elif target['type'] == 'lever':
            response = requests.get(target['url'], headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            for div in soup.find_all('div', class_='posting'):
                a = div.find('a', class_='posting-title')
                if a: jobs.append((a.find('h5').text.strip(), a['href']))

        elif target['type'] == 'ashby':
            slug = target['url'].split('/')[-1]
            api_url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
            response = requests.post(api_url, json={}, headers=headers)
            if response.status_code == 200:
                data = response.json()
                for job in data.get('jobs', []):
                    jobs.append((job['title'], job['jobUrl']))
            else:
                 print(f"  ❌ Ashby Error (Status {response.status_code})")

    except Exception as e:
        print(f"  ⚠️ Error: {e}")
        
    print(f"  -> Found {len(jobs)} jobs")
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
            body {{ font-family: -apple-system, system-ui, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f0f2f5; color: #1c1e21; margin: 0; padding: 20px; }}
            h1 {{ font-size: 24px; margin-bottom: 5px; color: #333; }}
            .timestamp {{ font-size: 13px; color: #65676b; margin-bottom: 25px; }}
            .card {{ background: white; border-radius: 12px; padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); transition: transform 0.2s; }}
            .card:active {{ transform: scale(0.98); }}
            .tag {{ display: inline-block; background: #e7f3ff; color: #1877f2; padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: 600; margin-bottom: 8px; }}
            .title {{ font-size: 17px; font-weight: 600; margin-bottom: 6px; display: block; text-decoration: none; color: #050505; line-height: 1.4; }}
            .new-badge {{ background: #e4f7eb; color: #09a244; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: 800; letter-spacing: 0.5px; margin-left: 8px; text-transform: uppercase; }}
            .meta {{ font-size: 13px; color: #65676b; margin-top: 8px; }}
            .empty {{ text-align: center; color: #65676b; margin-top: 60px; font-size: 15px; }}
        </style>
    </head>
    <body>
        <h1>🛏️ Bedtime Job Feed</h1>
        <div class="timestamp">Updated: {datetime.now().strftime("%B %d, %I:%M %p")}</div>
        
        {'<div class="empty">No matching jobs found today. Sleep well. 😴</div>' if not all_jobs else ''}
    """

    sorted_jobs = sorted(all_jobs.items(), key=lambda x: x[1]['date'], reverse=True)

    for link, job in sorted_jobs:
        is_new = link in new_jobs
        new_tag = '<span class="new-badge">FRESH</span>' if is_new else ''
        
        html_content += f"""
        <div class="card">
            <div><span class="tag">{job['company']}</span>{new_tag}</div>
            <a href="{link}" target="_blank" class="title">{job['title']}</a>
            <div class="meta">Found: {job['date']}</div>
        </div>
        """

    html_content += "</body></html>"
    
    with open("index.html", "w") as f:
        f.write(html_content)

# --- MAIN EXECUTION ---
def run():
    db = load_db()
    new_links = []
    
    print("--- Starting Job Hunt ---")
    for target in TARGETS:
        found = fetch_jobs(target)
        for title, link in found:
            # Check for keywords
            if any(k.lower() in title.lower() for k in KEYWORDS):
                if link not in db:
                    print(f"  ★ NEW MATCH: {title}")
                    db[link] = {
                        "company": target['name'],
                        "title": title,
                        "date": datetime.now().strftime("%Y-%m-%d")
                    }
                    new_links.append(link)
    
    save_db(db)
    generate_html(new_links, db)
    print("--- Dashboard Updated ---")

if __name__ == "__main__":
    run()
