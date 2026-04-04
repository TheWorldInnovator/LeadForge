import time
import math
from playwright.sync_api import sync_playwright
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


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
    - No fluff
    - No generic advice
    - DO NOT say "visit your website" or anything similar
    - DO NOT suggest the business take action themselves
    - Focus on missed patients or revenue loss
    - Sound confident, not needy

    CTA RULE:
    - End with ONE of these only:
    - "Worth a quick chat?"
    - "Open to a quick call?"
    - "Can I show you how?"
    - No other CTA allowed

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

        if not email or len(email) < 20:
            return f"""Hi {lead['Name']},

                        I came across your business and noticed strong potential to attract more clients.

                        With a few targeted SEO improvements and Google Ads, you could increase bookings consistently.

                        Would you be open to a quick call to explore?

                        Best,
                        [Your Name]"""

        return email

    except Exception as e:
        return f"Error: {e}"
    
def generate_display_reasoning_groq(lead):
    prompt = f"""
    Write ONE short professional sentence explaining why this business is a good lead for a marketing agency.

    Business: {lead['Name']}
    Rating: {lead['Rating']}
    Reviews: {lead['Reviews']}
    Website: {lead['Website'] or "No website"}
    Opportunity Score: {lead.get('Opportunity', 0)}
    Base Insight: {lead.get('Reasoning', 'No specific insight')}

    RULES:
    - Max 18 words
    - Professional
    - No fluff
    - No hype
    - No emojis
    - Mention only the strongest reason

    Write it now:
    """
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_completion_tokens=80,
            stream=False
        )

        reasoning = ""
        if completion.choices and completion.choices[0].message:
            reasoning = completion.choices[0].message.content or ""

        reasoning = reasoning.strip()

        if not reasoning or len(reasoning) < 10:
            return lead.get("Reasoning", "Strong opportunity for digital growth")

        return reasoning

    except Exception:
        return lead.get("Reasoning", "Strong opportunity for digital growth")


def generate_leads_logic(niche, city, progress_callback=None):
    def report(stage=None, progress=None, scraped=None, emails=None, total=None):
        if progress_callback:
            progress_callback(
                stage=stage,
                progress=progress,
                scraped=scraped,
                emails=emails,
                total=total
            )

    base_url = "https://maps.google.com/maps?hl=en"
    search_query = f"{niche} in {city}"

    data = []

    report(stage="Opening Google Maps", progress=5, scraped=0, emails=0, total=0)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(java_script_enabled=True)
        page = context.new_page()
        page.goto(base_url, wait_until="load")

        report(stage="Searching businesses", progress=10, scraped=0, emails=0, total=0)

        input_box = page.locator('//input[@name="q"]')
        input_box.fill(search_query)
        input_box.press("Enter")

        page.wait_for_selector('div[role="feed"]')
        time.sleep(5)

        report(stage="Loading results feed", progress=15, scraped=0, emails=0, total=0)

        results_panel = page.locator('div[role="feed"]')
        previous_count = 0

        while True:
            listings = page.locator('div[role="article"]')
            current_count = listings.count()

            if current_count == previous_count:
                break

            previous_count = current_count
            results_panel.evaluate("el => el.scrollBy(0, 2000)")
            time.sleep(2)

        for _ in range(5):
            results_panel.evaluate("el => el.scrollBy(0, 1000)")
            time.sleep(2)

        listings = page.locator('div[role="article"]')
        count = listings.count()

        report(stage="Scraping business details", progress=25, scraped=0, emails=0, total=count)

        seen_urls = set()
        scraped_businesses = 0

        for i in range(count):
            item = listings.nth(i)

            try:
                url = item.locator('a.hfpxzc').get_attribute('href')
            except:
                url = None

            if not url or url in seen_urls:
                continue

            seen_urls.add(url)

            new_page = context.new_page()
            try:
                new_page.goto(url, wait_until='domcontentloaded')

                try:
                    new_page.wait_for_selector('h1', timeout=8000)
                    new_page.wait_for_selector('button[data-item-id="address"]', timeout=8000)
                except:
                    pass

                try:
                    name = new_page.locator('h1').inner_text()
                except:
                    name = "N/A"

                try:
                    address = new_page.locator('button[data-item-id="address"]').inner_text()
                    address = address.replace("", "").strip()
                except:
                    address = "N/A"

                try:
                    rating = new_page.locator('span[aria-label*="stars"]').first.get_attribute("aria-label")
                except:
                    rating = "N/A"

                try:
                    phone = new_page.locator('button[data-item-id^="phone"]').inner_text()
                    phone = phone.replace("", "").strip()
                except:
                    phone = "N/A"

                try:
                    reviews = new_page.locator('span[aria-label*="reviews"]').first.get_attribute("aria-label")
                except:
                    reviews = "N/A"

                try:
                    website = new_page.locator('a[data-item-id="authority"]').get_attribute('href')
                except:
                    website = "N/A"

                data.append({
                    "Name": name,
                    "Rating": rating,
                    "Reviews": reviews,
                    "Address": address,
                    "Contact Number": phone,
                    "Website": website
                })

                scraped_businesses += 1
                detail_progress = 25 + int((scraped_businesses / max(count, 1)) * 35)
                report(
                    stage="Scraping business details",
                    progress=detail_progress,
                    scraped=scraped_businesses,
                    emails=0,
                    total=count
                )
            finally:
                new_page.close()

        browser.close()

    ratings = []
    reviews_list = []

    report(
        stage="Analyzing and scoring leads",
        progress=65,
        scraped=len(data),
        emails=0,
        total=len(data)
    )

    for d in data:
        try:
            d["Rating"] = float(d["Rating"].split()[0])
        except:
            d["Rating"] = 0

        try:
            d["Reviews"] = int(''.join(filter(str.isdigit, d["Reviews"])))
        except:
            d["Reviews"] = 0

        ratings.append(d["Rating"])
        reviews_list.append(d["Reviews"])

    for lead in data:
        website_value = "" if lead.get("Website", "N/A") in ["", "N/A"] else lead.get("Website", "")
        lead["Reasoning"] = generate_reasoning(
            lead.get("Rating", 0),
            lead.get("Reviews", 0),
            website_value
        )

    if not data:
        report(stage="Completed", progress=100, scraped=0, emails=0, total=0)
        return []

    min_rating, max_rating = min(ratings), max(ratings)
    min_reviews, max_reviews = min(reviews_list), max(reviews_list)

    for d in data:
        if max_rating != min_rating:
            norm_rating = (d["Rating"] - min_rating) / (max_rating - min_rating)
        else:
            norm_rating = 0.5

        if max_reviews != min_reviews:
            norm_reviews = (d["Reviews"] - min_reviews) / (max_reviews - min_reviews)
        else:
            norm_reviews = 0.5

        d["Score"] = round(0.5 * norm_rating + 0.5 * norm_reviews, 4)
        d["Opportunity"] = round(
            (0.7 * (1 - d["Rating"] / 5)) +
            (0.3 * math.log1p(d["Reviews"]) / math.log1p(max_reviews)),
            4
        )

    orderedclients = data.copy()
    orderedclients.sort(key=lambda x: x["Opportunity"], reverse=True)

    # remove duplicate leads before email generation + frontend output
    deduped_clients = []
    seen_keys = set()

    for lead in orderedclients:
        name = str(lead.get("Name", "")).strip().lower()
        address = str(lead.get("Address", "")).strip().lower()
        key = (name, address)

        if key in seen_keys:
            continue

        seen_keys.add(key)
        deduped_clients.append(lead)

    processed = set()
    total_email_targets = len(deduped_clients)
    generated_emails = 0

    report(
        stage="Generating outreach emails",
        progress=75,
        scraped=len(deduped_clients),
        emails=0,
        total=total_email_targets
    )

    for lead in deduped_clients:
        name = str(lead.get("Name", "")).strip()

        if name in processed:
            continue
        processed.add(name)

        lead["Website"] = "" if lead.get("Website") in ["N/A", None] else str(lead.get("Website")).strip()
        lead["Reviews"] = int(lead["Reviews"]) if isinstance(lead.get("Reviews"), (int, float)) else 0
        lead["Rating"] = float(lead["Rating"]) if isinstance(lead.get("Rating"), (int, float)) else 0
        lead["Reasoning"] = str(lead.get("Reasoning", "No specific insight")).strip()

        email = generate_email_groq(lead)

        if "Error" in email or len(email) < 30:
            email = generate_email_groq(lead)

        display_reasoning = generate_display_reasoning_groq(lead)

        lead["Email Copy"] = email
        lead["Display Reasoning"] = display_reasoning
        time.sleep(1)

        generated_emails += 1
        email_progress = 75 + int((generated_emails / max(total_email_targets, 1)) * 20)
        report(
            stage="Generating outreach emails",
            progress=email_progress,
            scraped=len(deduped_clients),
            emails=generated_emails,
            total=total_email_targets
        )

    final_leads = []

    report(
        stage="Finalizing results",
        progress=97,
        scraped=len(deduped_clients),
        emails=generated_emails,
        total=total_email_targets
    )

    for lead in deduped_clients:
        final_leads.append({
            "name": lead.get("Name", "Unknown Business"),
            "rating": lead.get("Rating", 0),
            "reviews": lead.get("Reviews", 0),
            "address": lead.get("Address", "N/A"),
            "contact_number": lead.get("Contact Number", "N/A"),
            "website": lead.get("Website", "N/A"),
            "opportunity": lead.get("Opportunity", 0),
            "email_copy": lead.get("Email Copy", "No outreach email available"),
            "display_reasoning": lead.get("Display Reasoning", lead.get("Reasoning", "No reasoning available"))
            
        })

    report(
        stage="Completed",
        progress=100,
        scraped=len(final_leads),
        emails=generated_emails,
        total=total_email_targets
    )

    return final_leads