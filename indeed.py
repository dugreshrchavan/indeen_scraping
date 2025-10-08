from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
import time 

app = Flask(__name__)

@app.route("/scrape_indeed/", methods=["GET"])
def scrape_indeed():
    keyword = request.args.get("keyword")
    location = request.args.get("location", "India")
    pages = int(request.args.get("pages", 1))

    if not keyword:
        return jsonify({"error": "Please provide a keyword"}), 400

    try:
        jobs = []

        # Setup Chrome
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        for page in range(pages):
            start = page * 10
            indeed_url = f"https://www.indeed.com/jobs?q={keyword.replace(' ', '+')}&l={location.replace(' ', '+')}&start={start}"
            driver.get(indeed_url)

            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.job_seen_beacon"))
            )
            time.sleep(1.5)

            soup = BeautifulSoup(driver.page_source, "html.parser")

            for job in soup.select("div.job_seen_beacon"):
                title_tag = job.select_one("h2.jobTitle span")
                company_tag = job.select_one("span.companyName")
                location_tag = job.select_one("div.companyLocation")
                salary_tag = job.select_one("div.salary-snippet-container")
                summary_tag = job.select_one("div.job-snippet")
                date_tag = job.select_one("span.date")
                apply_link_tag = job.select_one("a")

                company_name = ""
                if company_tag:
                    link_tag = company_tag.select_one("a")
                    company_name = link_tag.text.strip() if link_tag else company_tag.text.strip()

                apply_link = (
                    "https://www.indeed.com" + apply_link_tag["href"]
                    if apply_link_tag and apply_link_tag.has_attr("href")
                    else ""
                )

                jobs.append({
                    "jobTitle": title_tag.text.strip() if title_tag else "",
                    "company": company_name,
                    "location": location_tag.text.strip() if location_tag else "",
                    "salary": salary_tag.text.strip() if salary_tag else "Not disclosed",
                    "summary": summary_tag.text.strip() if summary_tag else "",
                    "postedDate": date_tag.text.strip() if date_tag else "",
                    "applyLink": apply_link,
                    "platform": "Indeed"
                })

        driver.quit()

        return jsonify({
            "platform": "Indeed",
            "keyword": keyword,
            "location": location,
            "totalJobs": len(jobs),
            "jobs": jobs
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
