import time
import math
from playwright.sync_api import sync_playwright

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_email_groq(lead):
    prompt = f"""
Write a short cold outreach email FROM a marketing/ad agency TO a local business.

Business name: {lead.get("Name") or lead.get("name")}
Rating: {lead.get("Rating") or lead.get("rating")}
Reviews: {lead.get("Reviews") or lead.get("reviews")}
Website: {lead.get("Website") or lead.get("website") or "No website"}
Lead insight: {lead.get("Reasoning") or lead.get("display_reasoning")}

Rules:
- Under 60 words
- No subject line
- No "Dear [Recipient]"
- Do NOT pretend to be the business
- Do NOT say "our clinic", "our team", "visit us", or "we provide care"
- Speak as an agency offering ads/SEO/lead generation
- Make it relevant to any business type, not only dentists
- Mention missed customers or growth opportunity
- End with exactly: Worth a quick chat?

Write the email now.
"""

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_completion_tokens=90,
            stream=False
        )

        return completion.choices[0].message.content.strip()

    except Exception as e:
        print("Groq error:", e)
        return f"Error generating email: {e}"

def clean_text(value):
    if not value:
        return "N/A"
    return (
        str(value)
        .replace("", "")
        .replace("", "")
        .replace("\ue0c8", "")
        .replace("\ue0b0", "")
        .replace("\n", " ")
        .strip()
    )


def generate_reasoning(rating, reviews, website):
    if rating < 4.0:
        return "Low rating - business may need reputation improvement"
    elif reviews < 50:
        return "Low review count - growth opportunity"
    elif website in ["", "N/A", None]:
        return "No website - strong opportunity for digital services"
    return "Good profile but may still benefit from ads/SEO"


def generate_leads_logic(niche, city, progress_callback=None, max_results=50):
    def report(stage=None, progress=None, scraped=None, emails=0, total=None):
        if progress_callback:
            progress_callback(stage=stage, progress=progress, scraped=scraped, emails=emails, total=total)

    search_query = f"{niche} in {city}"
    data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 900}, locale="en-US")
        page = context.new_page()

        report("Opening Google Maps", 5, 0, 0, max_results)

        page.goto("https://maps.google.com/maps?hl=en", wait_until="domcontentloaded")

        page.locator('//input[@name="q"]').fill(search_query)
        page.keyboard.press("Enter")

        page.wait_for_selector('div[role="feed"]', timeout=20000)
        feed = page.locator('div[role="feed"]')

        previous_count = 0
        no_growth = 0

        while True:
            listings = page.locator('div[role="article"]')
            current_count = listings.count()

            print("Loaded listings:", current_count)

            if current_count >= max_results:
                break

            if current_count == previous_count:
                no_growth += 1
            else:
                no_growth = 0

            if no_growth >= 8:
                break

            previous_count = current_count
            feed.evaluate("el => el.scrollBy(0, 5000)")
            page.wait_for_timeout(900)

        listings = page.locator('div[role="article"]')
        count = min(listings.count(), max_results)

        urls = []
        seen = set()

        for i in range(count):
            try:
                url = listings.nth(i).locator("a.hfpxzc").get_attribute("href", timeout=3000)
                if url and url not in seen:
                    seen.add(url)
                    urls.append(url)
            except:
                pass

        report("Scraping business details", 25, 0, 0, len(urls))

        for index, url in enumerate(urls, start=1):
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(2500)
            except:
                continue

            try:
                name = clean_text(page.locator("h1.DUwDvf").inner_text(timeout=2500))
            except:
                try:
                    name = clean_text(page.locator("h1").inner_text(timeout=2500))
                except:
                    name = "N/A"

            try:
                address = clean_text(page.locator('button[data-item-id="address"]').inner_text(timeout=2500))
            except:
                address = "N/A"

            try:
                phone = clean_text(page.locator('button[data-item-id^="phone"]').inner_text(timeout=2500))
            except:
                phone = "N/A"

            try:
                page.wait_for_selector("div.F7nice", timeout=6000)
    
            except:
                pass

            rating_raw = "N/A"
            reviews_raw = "N/A"

            try:
                rating_raw = page.locator("div.F7nice span[aria-hidden='true']").first.inner_text(timeout=4000)
            except:
                try:
                    rating_raw = page.locator("span[aria-label*='stars']").first.get_attribute("aria-label", timeout=4000)
                except:
                    rating_raw = "N/A"

            try:
                reviews_raw = page.locator("div.F7nice span[aria-label*='reviews']").first.get_attribute("aria-label", timeout=4000)
            except:
                try:
                    reviews_raw = page.locator("button[jsaction*='pane.reviewChart.moreReviews']").first.get_attribute("aria-label", timeout=4000)
                except:
                    reviews_raw = "N/A"
            try:
                website = page.locator('a[data-item-id="authority"]').get_attribute("href", timeout=2500)
                website = website.split("?")[0].rstrip("/") if website else "N/A"
            except:
                website = "N/A"

            try:
                rating = float(str(rating_raw).split()[0])
            except:
                rating = 0

            try:
                reviews = int("".join(filter(str.isdigit, str(reviews_raw))))
            except:
                reviews = 0

            data.append({
                "Name": name,
                "Rating": rating,
                "Reviews": reviews,
                "Address": address,
                "Contact Number": phone,
                "Website": website,
            })

            report(
                "Scraping business details",
                25 + int((index / max(len(urls), 1)) * 60),
                len(data),
                0,
                len(urls)
            )

        browser.close()

    if not data:
        return []

    ratings = [d["Rating"] for d in data]
    reviews_list = [d["Reviews"] for d in data]

    min_rating, max_rating = min(ratings), max(ratings)
    min_reviews, max_reviews = min(reviews_list), max(reviews_list)

    for d in data:
        norm_rating = (d["Rating"] - min_rating) / (max_rating - min_rating) if max_rating != min_rating else 0.5
        norm_reviews = (d["Reviews"] - min_reviews) / (max_reviews - min_reviews) if max_reviews != min_reviews else 0.5

        d["Score"] = round(0.5 * norm_rating + 0.5 * norm_reviews, 4)
        d["Opportunity"] = round(
            (0.7 * (1 - d["Rating"] / 5)) +
            (0.3 * math.log1p(d["Reviews"]) / math.log1p(max(max_reviews, 1))),
            4
        )
        d["Reasoning"] = generate_reasoning(d["Rating"], d["Reviews"], d["Website"])

    data.sort(key=lambda x: x["Opportunity"], reverse=True)

    final_leads = []
    seen_keys = set()

    for lead in data:
        key = (
            str(lead["Name"]).strip().lower(),
            str(lead["Address"]).strip().lower()
        )

        if key in seen_keys:
            continue

        seen_keys.add(key)

        final_leads.append({
            "name": lead["Name"],
            "rating": lead["Rating"],
            "reviews": lead["Reviews"],
            "address": lead["Address"],
            "contact_number": lead["Contact Number"],
            "website": lead["Website"],
            "opportunity": lead["Opportunity"],
            "score": lead["Score"],
            "email_copy": "",
            "display_reasoning": lead["Reasoning"]
        })

    return final_leads


if __name__ == "__main__":
    start = time.time()

    leads = generate_leads_logic(
        niche="dentist",
        city="Dubai",
        max_results=50
    )

    end = time.time()

    print(f"\nScraped {len(leads)} leads")
    print(f"Time taken: {round(end - start, 2)} seconds\n")

    for lead in leads[:]:
        print(lead)
        print("-" * 50)