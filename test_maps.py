import time
from playwright.sync_api import sync_playwright
import csv
import math
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
base_url='https://maps.google.com/maps?hl=en'
search_query='Dentists in Dubai'

playwright=sync_playwright().start()
browser=playwright.chromium.launch(headless=False)
context=browser.new_context(java_script_enabled=True)
page=context.new_page()
page.goto(base_url, wait_until='load')

# find search box
input_box = page.locator('//input[@name="q"]')
input_box.fill(search_query)
input_box.press('Enter')

# wait for results
page.wait_for_selector('div[role="feed"]')
time.sleep(5)

# scroll results panel
# infinite scroll
results_panel = page.locator('div[role="feed"]')

previous_count = 0

while True:
    listings = page.locator('div[role="article"]')
    current_count = listings.count()

    print(f"Loaded: {current_count}")

    if current_count == previous_count:
        print("No more new results. Stopping scroll.")
        break

    previous_count = current_count

    # scroll down
    results_panel.evaluate("el => el.scrollBy(0, 2000)")
    time.sleep(2)
listings = page.locator('div[role="article"]')
count = listings.count()
print(f"Final count: {count}")

for i in range(5):
    results_panel.evaluate("el => el.scrollBy(0, 1000)")
    time.sleep(2)

# ✅ GET ALL LISTINGS
listings = page.locator('div[role="article"]')
count = listings.count()
print(f"Found {count} listings")

# ✅ SCRAPE DATA
seen_urls = set()
result_index = 1

data = []
for i in range(count):
    item = listings.nth(i)

    # ✅ get correct business URL
    try:
        url = item.locator('a.hfpxzc').get_attribute('href')
    except:
        url = None

    if not url or url in seen_urls:
        continue

    seen_urls.add(url)

    # open new tab
    new_page = context.new_page()
    new_page.goto(url, wait_until='domcontentloaded')

    # ✅ wait properly (no blind sleep)
    try:
        new_page.wait_for_selector('h1', timeout=8000)
        new_page.wait_for_selector('button[data-item-id="address"]', timeout=8000)
    except:
        print(f"Load failed: {url}")

    # name
    try:
        name = new_page.locator('h1').inner_text()
    except:
        name = "N/A"

    # address
    try:
        address = new_page.locator('button[data-item-id="address"]').inner_text()
        address = address.replace("","").strip()
    except:
        address = "N/A"

    # rating
    try:
        rating = new_page.locator('span[aria-label*="stars"]').first.get_attribute("aria-label")
    except:
        rating = "N/A"
    
    # phone number
    try:
        phone = new_page.locator('button[data-item-id^="phone"]').inner_text()
        phone = phone.replace("", "").strip()
    except:
        phone = "N/A"
    
    # reviews
    try:
        reviews = new_page.locator('span[aria-label*="reviews"]').first.get_attribute("aria-label")
    except:
        reviews = "N/A"

    # website
    try:
        website = new_page.locator('a[data-item-id="authority"]').get_attribute('href')
    except:
        website = "N/A"
    
    
    
    print(f"{result_index}. {name}")
    print(f"   Rating: {rating}")
    print(f"   Reviews: {reviews}")
    print(f"   Address: {address}")
    print(f"   Contact Number: {phone}")
    print(f"   Website: {website}")
    print("---------------------")
    data.append({
        "Name":name,
        "Rating":rating,
        "Reviews":reviews,
        "Address":address,
        "Contact Number":phone,
        "Website":website
    })


    result_index += 1
    new_page.close()


# Convert scraped ratings and reviews to numeric
ratings = []
reviews = []

for d in data:
    try:
        d["Rating"] = float(d["Rating"].split()[0])  # remove 'stars' text if present
    except:
        d["Rating"] = 0
    try:
        d["Reviews"] = int(''.join(filter(str.isdigit, d["Reviews"])))  # extract numbers
    except:
        d["Reviews"] = 0

    ratings.append(d["Rating"])
    reviews.append(d["Reviews"])

# --- ADD REASONING ---
def generate_reasoning(rating, reviews, website):
    try:
        rating = float(rating)
    except:
        rating = 0
    try:
        reviews = int(reviews)
    except:
        reviews = 0

    if rating < 4.0:
        return "Low rating - business may need reputation improvement"
    elif reviews < 50:
        return "Low review count - growth opportunity"
    elif website in ["", "N/A", None]:
        return "No website - strong opportunity for digital services"
    else:
        return "Good profile but may still benefit from ads/SEO"
    
def generate_email_groq(lead):
    prompt = f"""
    Write a short, high-converting cold email.

    Business: {lead['Name']}
    Rating: {lead['Rating']}
    Reviews: {lead['Reviews']}
    Website: {lead['Website'] or "No website"}
    Insight: {lead['Reasoning']}

    RULES:
    - Max 60 words
    - No questions like "are you getting..."
    - No fluff
    - Mention missed patients or revenue
    - Sound confident, not needy
    - End with a soft CTA (not pushy)

    FORMAT:
    Hi {lead['Name']},

    [Observation]
    [Missed opportunity]
    [Simple fix hint]
    [CTA]

    Write it now:
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_completion_tokens=300,
            stream=False
        )

        email = ""
        if completion.choices and completion.choices[0].message:
            email = completion.choices[0].message.content or ""

        email = email.strip()

        # fallback if model fails
        if not email or len(email) < 20:
            return f"""Hi {lead['Name']},

I came across your clinic and noticed strong potential to attract more local patients.

With a few targeted SEO improvements and Google Ads, you could increase bookings consistently.

Would you be open to a quick call to explore?

Best,
[Your Name]"""

        return email  # 🔥 THIS WAS MISSING

    except Exception as e:
        return f"Error: {e}"

for lead in data:
    website_value = "" if lead.get("Website", "N/A") in ["", "N/A"] else lead.get("Website", "")
    lead["Reasoning"] = generate_reasoning(
        lead.get("Rating", 0),
        lead.get("Reviews", 0),
        website_value
    )

min_rating, max_rating = min(ratings), max(ratings)
min_reviews, max_reviews = min(reviews), max(reviews)





for d in data:
    # Normalize rating and reviews
    if max_rating != min_rating:
        norm_rating = (d["Rating"] - min_rating) / (max_rating - min_rating)
    else:
        norm_rating = 0.5  # if all ratings same
    
    if max_reviews != min_reviews:
        norm_reviews = (d["Reviews"] - min_reviews) / (max_reviews - min_reviews)
    else:
        norm_reviews = 0.5  # if all reviews same
    
    # Neutral score (0.0 to 1.0)
    d["Score"] = round(0.5 * norm_rating + 0.5 * norm_reviews, 4)
    #opportunity score
    d["Opportunity"] = round(
    (0.7 * (1 - d["Rating"]/5)) + 
    (0.3 * math.log1p(d["Reviews"]) / math.log1p(max_reviews)),
    4)




orderedscore=data.copy()
orderedclients=data.copy()
orderedscore.sort(key=lambda x: x["Score"], reverse=True)  #ranking best businesses
orderedclients.sort(key=lambda x: x["Opportunity"], reverse=True)   #ranking best clients for monetization

print("\n--- GENERATING OUTREACH FOR TOP 3 LEADS ---\n")

processed = set()

for lead in orderedclients:

    name = str(lead.get('Name','')).strip()

    # 🔥 prevent duplicate processing
    if name in processed:
        continue
    processed.add(name)

    lead['Website'] = (
    "" if lead.get('Website') in ["N/A", None] else str(lead.get('Website')).strip()
    )
    lead['Reviews'] = (
        int(lead['Reviews']) if isinstance(lead.get('Reviews'), (int, float)) else 0
    )

    lead['Rating'] = (
        float(lead['Rating']) if isinstance(lead.get('Rating'), (int, float)) else 0
    )
    lead['Reasoning'] = str(lead.get('Reasoning','No specific insight')).strip()

    email = generate_email_groq(lead)
    lead["Email Copy"] = email

    # retry once
    if "Error" in email or len(email) < 30:
        print(f"Retrying for {name}...")
        email = generate_email_groq(lead)

    print(f"\nLead: {name}")
    print("Outreach Email:\n")
    print(email)
    print("\n-----------------------------\n")

    time.sleep(1)  # 🔥 prevents API weirdness
#bestbusinessescsv
with open("bestbusinesses.csv","w",newline="",encoding="utf-8-sig") as f:
    writer=csv.DictWriter(f, fieldnames=orderedscore[0].keys())
    writer.writeheader()
    writer.writerows(orderedscore)

#bestclientscsv
with open("bestclients.csv","w",newline="",encoding="utf-8-sig") as f:
    writer=csv.DictWriter(f, fieldnames=orderedclients[0].keys())
    writer.writeheader()
    writer.writerows(orderedclients)

print("Leads will be saved to dubaidentists.csv")
print("Browser will stay open for 60 seconds...")
time.sleep(60)

browser.close()
playwright.stop()