# Product Requirements Document: LinkedIn Job Alert Automation

## Overview

A lightweight personal automation tool that monitors LinkedIn job search results every 20 minutes and delivers new job postings directly to the user via WhatsApp. The goal is to surface relevant opportunities as early as possible so the user can be among the first to apply.

---

## Problem Statement

LinkedIn surfaces job postings chronologically, but checking manually throughout the day means missing early windows on fresh postings. Being one of the first applicants significantly increases the chance of being seen by recruiters. A 20-minute polling cycle closes this gap without requiring constant manual checking.

---

## Goals

- Automatically scrape the first page of a LinkedIn job search every 20 minutes
- Send only new (not previously seen) job postings to the user via WhatsApp
- Support LinkedIn boolean search syntax and filters (remote, sort by most recent)
- Require minimal ongoing maintenance once set up

---

## Non-Goals

- Automatically applying to jobs
- Scraping beyond the first page of results
- Supporting multiple users
- Building a web UI or dashboard
- Storing or analysing job data long-term

---

## User

Solo user (the developer themselves). Technical enough to run a Python script and set up a cron job.

---

## Functional Requirements

### Job Scraping
- Use Playwright with a persistent browser context to authenticate as the user on LinkedIn
- On first run: open a visible browser window so the user can log in manually; save the session for all future runs
- On subsequent runs: run headlessly using the saved session
- Navigate to a configurable LinkedIn job search URL (encodes boolean keywords, location, remote filter, sort by most recent)
- Extract from each job card on the first page:
  - Job ID (for deduplication)
  - Job title
  - Company name
  - Location
  - Time posted
  - Direct job URL
- For each new job, navigate to the job detail page and extract the job description (truncated to ~400 characters for readability)

### Deduplication
- Maintain a local `seen_jobs.json` file storing IDs of all jobs already sent
- On each run, only process and send jobs whose IDs are not in this file
- Append new job IDs to the file after successfully sending

### WhatsApp Messaging (CallMeBot)
- Use the CallMeBot WhatsApp API to send messages (free tier, HTTP request based)
- Send one WhatsApp message per new job in the format:

```
*[Job Title]* @ [Company]
[Location] • [Time Posted]
[Job URL]

[Description excerpt ~400 chars...]
```

- Add a short delay between messages to avoid rate limiting
- If no new jobs are found, send nothing (no noise)

### Scheduling
- Run via macOS `crontab` every 20 minutes
- Script should be fully non-interactive after the first login run

### Configuration
- All user-specific values stored in a `.env` file (not committed to version control):
  - `LINKEDIN_SEARCH_URL` — the full job search URL with filters
  - `CALLMEBOT_PHONE` — user's phone number with country code
  - `CALLMEBOT_APIKEY` — API key received from CallMeBot setup

---

## Technical Stack

| Component | Choice | Reason |
|---|---|---|
| Language | Python 3 | Broad library support, simple scripting |
| Browser automation | Playwright (async) | Handles JS-rendered pages, supports persistent sessions |
| HTTP requests | `requests` | CallMeBot API calls |
| Deduplication store | JSON file | Zero dependencies, sufficient for personal use |
| Scheduling | macOS crontab | Native, no extra tooling |
| Messaging | CallMeBot WhatsApp API | Free, minimal setup, no account required |

---

## File Structure

```
jobAutomation/
├── PRD.md               # This document
├── scraper.py           # Main script
├── requirements.txt     # Python dependencies
├── .env                 # User config (not committed)
├── .env.example         # Template for .env
├── seen_jobs.json       # Auto-generated deduplication store
└── session/             # Auto-generated Playwright session data
```

---

## Setup Flow (First Time)

1. Install dependencies: `pip install -r requirements.txt && playwright install chromium`
2. Copy `.env.example` to `.env` and fill in values
3. Set up CallMeBot: add their number on WhatsApp and get an API key
4. Run `python scraper.py --login` to open the browser and log in to LinkedIn manually
5. Add the cron job: `*/20 * * * * /usr/bin/python3 /path/to/scraper.py`

---

## Risk & Mitigations

| Risk | Mitigation |
|---|---|
| LinkedIn detects automation | Use real Chromium browser with persistent session; add random delays between actions (2–4s); only scrape first page at low frequency |
| Session expires | Script detects if redirected to login page and exits with a clear error message prompting the user to re-run with `--login` |
| CallMeBot rate limits | Small delay between messages; batching not needed at typical job volumes (0–10 new jobs per run) |
| Duplicate messages | `seen_jobs.json` deduplication prevents re-sending across all runs |
