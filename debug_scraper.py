import requests

# The target that is currently failing for you
target_url = "https://boards.greenhouse.io/datadog"
jina_url = f"https://r.jina.ai/{target_url}"

print(f"🕵️ DEBUGGING: {target_url}")
print("-" * 40)

try:
    response = requests.get(jina_url)
    
    # 1. Check the Status Code
    print(f"👉 Status Code: {response.status_code}")
    
    # 2. Check the "Real" Content
    # We print the first 500 characters to see if it's a Captcha or real content
    content_snippet = response.text[:500]
    print(f"\n👉 Raw Response Snippet:\n{content_snippet}")
    
    # 3. Keyword Check
    if "Cloudflare" in response.text or "Just a moment" in response.text:
        print("\n🚨 DIAGNOSIS: BLOCKED BY CLOUDFLARE")
        print("   (They are serving a 'Waiting Room' page instead of the jobs)")
        
    elif "Access denied" in response.text or "403 Forbidden" in response.text:
        print("\n🚨 DIAGNOSIS: HARD IP BLOCK")
        print("   (They rejected your request entirely)")
        
    elif len(response.text) < 1000:
        print("\n⚠️ DIAGNOSIS: SUSPICIOUSLY SHORT CONTENT")
        print("   (Real job pages are usually huge. This is likely an error page)")
        
    else:
        print("\n✅ DIAGNOSIS: LOOKS OKAY?")
        print("   (If this says OK but you see no jobs, our parsing logic is wrong)")

except Exception as e:
    print(f"❌ CRITICAL ERROR: {e}")
