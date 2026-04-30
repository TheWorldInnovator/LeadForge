from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from lead_generator import generate_leads_logic, generate_email_groq
from pydantic import BaseModel
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

job_status = "idle"
job_stage = "Not started"
job_progress = 0
scraped_count = 0
email_count = 0
total_target = 0
leads_data = []
job_error = None


def update_progress(stage=None, progress=None, scraped=None, emails=None, total=None):
    global job_stage, job_progress, scraped_count, email_count, total_target

    if stage is not None:
        job_stage = stage
    if progress is not None:
        job_progress = progress
    if scraped is not None:
        scraped_count = scraped
    if emails is not None:
        email_count = emails
    if total is not None:
        total_target = total


def run_generation_job(niche, city):
    global job_status, leads_data, job_error
    global job_stage, job_progress, scraped_count, email_count, total_target

    try:
        job_status = "running"
        job_error = None
        leads_data = []
        job_stage = "Starting..."
        job_progress = 0
        scraped_count = 0
        email_count = 0
        total_target = 0

        results = generate_leads_logic(
            niche=niche,
            city=city,
            progress_callback=update_progress,
            max_results=100)

        leads_data = results
        job_status = "completed"
        job_stage = "Completed"
        job_progress = 100

    except Exception as e:
        job_status = "error"
        job_error = str(e)
        job_stage = "Failed"


class LeadRequest(BaseModel):
    niche: str
    city: str

@app.post("/generate-leads")
def generate_leads(request: LeadRequest, background_tasks: BackgroundTasks):
    global job_status

    if job_status == "running":
        return {"message": "Lead generation already running", "status": job_status}

    background_tasks.add_task(run_generation_job, request.niche, request.city)
    return {"message": "Lead generation started", "status": "running"}


@app.get("/status")
def get_status():
    return {
        "status": job_status,
        "stage": job_stage,
        "progress": job_progress,
        "scraped_count": scraped_count,
        "email_count": email_count,
        "total_target": total_target,
        "count": len(leads_data),
        "error": job_error
    }


@app.get("/leads")
def get_leads():
    return leads_data

@app.post("/generate-email")
def generate_email(lead: dict):
    email = generate_email_groq(lead)
    return {"email": email}