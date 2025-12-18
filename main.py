import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

# --- CONFIGURATION ---
TARGETS = [
    {"name": "Datadog", "url": "https://boards.greenhouse.io/datadog", "type": "greenhouse"},
    {"name": "Anduril", "url": "https://boards.greenhouse.io/andurilindustries", "type": "greenhouse"},
    {"name": "Palantir", "url": "https://jobs.lever.co/palantir", "type": "lever"},
    {"name": "Linear", "url": "https://jobs.ashbyhq.com/linear", "type": "ashby"},
    {"name": "Rippling", "url": "https://jobs.ashbyhq.com/rippling", "type": "ashby"},
    {"name": "Vannevar Labs", "url": "https://jobs.ashbyhq.com/vannevarlabs", "type": "ashby"},
    # ... add the rest of your list here
]

KEYWORDS = ["Solutions Engineer", "Sales Engineer", "Forward Deployed", "Deployment"]
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
    try:
        if target['type'] == 'greenhouse':
            soup = BeautifulSoup(requests.get(target['url']).text, 'html.parser')
            for div in soup.find_all('div', class_='opening'):
                a = div.find('a')
                if a: jobs.append((a.text.strip(), "https://boards.greenhouse.io" + a['href']))
        
        elif target['type'] == 'lever':
            soup = BeautifulSoup(requests.get(target['url']).text, 'html.parser')
            for div in soup.find_all('div', class_='posting'):
                a = div.find('a', class_='posting-title')
                if a: jobs.append((a.find('h5').text.strip(), a['href']))

        elif target['type'] == 'ashby':
            slug = target['url'].split('/')[-1]
            data = requests.post(f"https://api.ashbyhq.com/posting-api/job-board/{slug}", json={}).json()
            for job in data.get('jobs', []):
                jobs.append((job['title'], job['jobUrl']))
    except:
        pass # Silently fail to keep the dashboard clean
    return jobs

# --- HTML GENERATOR ---
def generate_html(new_jobs, all_jobs):
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #f4f4f9; color: #333; margin: 0; padding: 20px; }}
            h1 {{ font-size: 24px; margin-bottom: 5px; }}
            .timestamp {{ font-size: 12px; color: #666; margin-bottom: 20px; }}
            .card {{ background: white; border-radius: 12px; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
            .tag {{ display: inline-block; background: #e0e7ff; color: #4338ca; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: bold; margin-bottom: 8px; }}
            .title {{ font-size: 16px; font-weight: 600; margin-bottom: 5px; display: block; text-decoration: none; color: #111; }}
            .new-badge {{ background: #dcfce7; color: #166534; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: bold; margin-left: 10px; }}
            .empty {{ text-align: center; color: #888; margin-top: 40px; }}
        </style>
    </head>
    <body>
        <h1>🛏️ Bedtime Job Feed</h1>
        <div class="timestamp">Updated: {datetime.now().strftime("%B %d, %I:%M %p")}</div>
        
        {'<div class="empty">No matching jobs found yet.</div>' if not all_jobs else ''}
    """

    # Sort jobs by date found (newest first)
    sorted_jobs = sorted(all_jobs.items(), key=lambda x: x[1]['date'], reverse=True)

    for link, job in sorted_jobs:
        is_new = link in new_jobs
        new_tag = '<span class="new-badge">FRESH</span>' if is_new else ''
        
        html_content += f"""
        <div class="card">
            <span class="tag">{job['company']}</span> {new_tag}
            <a href="{link}" target="_blank" class="title">{job['title']}</a>
            <div style="font-size: 12px; color: #888; margin-top: 5px;">Found: {job['date']}</div>
        </div>
        """

    html_content += "</body></html>"
    
    with open("index.html", "w") as f:
        f.write(html_content)

# --- MAIN EXECUTION ---
def run():
    db = load_db()
    new_links = []
    
    for target in TARGETS:
        print(f"Scanning {target['name']}...")
        found = fetch_jobs(target)
        for title, link in found:
            if any(k.lower() in title.lower() for k in KEYWORDS):
                if link not in db:
                    db[link] = {
                        "company": target['name'],
                        "title": title,
                        "date": datetime.now().strftime("%Y-%m-%d")
                    }
                    new_links.append(link)
    
    save_db(db)
    generate_html(new_links, db)
    print("Dashboard updated.")

if __name__ == "__main__":
    run()
