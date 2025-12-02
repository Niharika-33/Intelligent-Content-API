# The Intelligent Content API

## Backend Engineering Intern Assignment: Full Stack Microservice Implementation (FastAPI + MySQL + Gemini)

## 1. Setup and Local Execution

This project is fully containerized using Docker to guarantee a consistent, portable environment.

### Prerequisites

1. Git: Installed and configured.
2. Docker Desktop: Installed and running (required for containerization).
3. Gemini API Key: A free key generated from Google AI Studio (required for AI functionality).

### Step 1: Clone the Repository and Configure Secrets

# Clone the repository
git clone https://github.com/Niharika-33/Intelligent-Content-API.git
cd Intelligent-Content-API

# Create a local .env file (File is .gitignored for security)
cp .env.example .env

Generate Secure JWT Key (SECRET_KEY):

Generate a secure, 32 character random string to use as your SECRET_KEY in the .env file:

```bash
python -c 'import secrets; print(secrets.token_urlsafe(32))'

### Crucial Checkpoint: Update the `.env` file

| Variable | Purpose | Cross Check Status |
|----------|----------|---------------------|
| DATABASE_URL Password | MySQL DB Password | Must EXACTLY match the password set in docker compose.yml. |
| SECRET_KEY | JWT signing key (32+ random characters) | Must be long and random. |
| GEMINI_API_KEY | Your Google Gemini API Key | Must be the actual key starting with AIzaSy... (Crucial for LLM function). |

### Step 2: Build and Run the Stack

Run this single command from the root directory. It builds the FastAPI container, starts the MySQL container, and manages the dependency sequence.

# Builds the web service and starts the MySQL container
docker compose up -d --build

When finished, stop the containers:

docker compose down

### Step 3: Verification and Access

* Documentation URL (Swagger UI): http://localhost:8000/docs  
* API Root URL: http://localhost:8000/api/v1

## 2. API Endpoints & Functional Flow

All critical API logic is protected and located within the `/api/v1` router.

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| POST | /api/v1/signup | Registers a new user. | Public |
| POST | /api/v1/login | Authenticates user (using form data for Swagger UI) and returns the JWT access_token. | Public |
| POST | /api/v1/contents | Core Feature: Saves content, triggers asynchronous LLM analysis, and updates the record with results. | Requires JWT |
| GET | /api/v1/contents | Retrieves all content owned by the authenticated user (tested working). | Requires JWT |
| DELETE | /api/v1/contents/{id} | Deletes a specific piece of content (confirmed working). | Requires JWT |

## 3. Design Decisions & Technical Overview

### A. Core Technical Stack

| Component | Technology | Rationale |
|-----------|-------------|-----------|
| Framework | FastAPI (Python 3.11) | Chosen for its high performance, asynchronous capabilities (ideal for handling I/O-bound LLM waiting periods). |
| Database | MySQL + Async SQLAlchemy | Used a single relational DB for persistence. Robust Docker Health Checks were implemented to resolve complex startup dependency issues. |
| Authentication | JWT / SHA256 | Standard security protocol. SHA256 hashing was implemented to bypass external C library conflicts (like bcrypt) found in the container environment. |

### B. LLM Integration: Transition to Gemini Structured Output

The final integration uses the Google Gemini API (under the Google Vertex AI mandate) to ensure stability, resolving previous issues with external service path changes.

LLM Workflow: The Python service makes a single asynchronous request to the Gemini API. This request is designed with a JSON Schema instructing Gemini to perform both Summarization and Sentiment Analysis and return the result in a clean, validated JSON structure. This method eliminated fragile, multi-step API calls and manual data parsing.

### C. GCP Deployment Architecture (Theoretical)

The proposed production architecture leverages serverless computing to ensure high availability and automatic scaling.

| Component | GCP Service | Role & Justification |
|-----------|--------------|----------------------|
| Backend API (FastAPI) | Cloud Run | Serverless deployment of the Docker container. Scales automatically and efficiently handles the I/O-bound wait time for the Gemini service. |
| Database (MySQL) | Cloud SQL | Fully managed persistent data layer, separated from the stateless API. |
| Security & Traffic | API Gateway | Enforces security policies (JWT validation, rate limits) at the edge before traffic reaches the Cloud Run service. |
| CI/CD | GitHub Actions / Artifact Registry | Automates Docker image build, secure storage, and triggers reliable deployment to Cloud Run. |
