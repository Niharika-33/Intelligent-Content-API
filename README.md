🧠 The Intelligent Content API

Backend Engineering Intern Assignment

This project delivers a complete, containerized RESTful API built with Python's FastAPI framework. It securely manages user content and leverages the Google Gemini LLM for asynchronous summarization and sentiment analysis.

🚀 1. Setup Instructions (Local & Docker)

Prerequisites

Git: Installed and configured.

Docker Desktop: Installed and running (essential for MySQL and application containerization).

Gemini API Key: A free key generated from Google AI Studio (required to bypass network permission errors).

Step 1: Clone the Repository & Configure

# Clone the repository
git clone [https://github.com/DevNiha/Intelligent-Content-API.git](https://github.com/DevNiha/Intelligent-Content-API.git)
cd Intelligent-Content-API

# Copy the example environment file and fill in secrets
cp .env.example .env


Update the .env file: Replace placeholders with your actual secure values.

Variable

Purpose

Value to Set

DATABASE_URL

MySQL Connection String

mysql+aiomysql://root:MyStrongDockerDBPass123@db:3306/content_db

SECRET_KEY

JWT signing key (32+ random characters)

[GENERATED_RANDOM_STRING]

GEMINI_API_KEY

Your Google Gemini API Key (AIzaSy...)

[YOUR_GEMINI_KEY]

Step 2: Build and Run with Docker Compose

This command handles building the image, starting the database, and managing the startup dependency (ensuring the API waits for the database to be ready).

docker compose up -d --build


Step 3: Stop the Application

When you are finished, stop and remove the containers:

docker compose down


🛠️ 2. API Documentation (Swagger UI)

The API automatically generates interactive documentation compliant with OpenAPI (Swagger UI).

Docs URL: http://localhost:8000/docs

Key Endpoints

Method

Endpoint

Description

Authentication

POST

/api/v1/signup

Registers a new user account.

Public

POST

/api/v1/login

Authenticates user and returns a JWT access_token. (Uses form data input).

Public

POST

/api/v1/contents

Saves content to DB & Triggers AI analysis for summary/sentiment.

Requires JWT

GET

/api/v1/contents

Retrieves all content submitted by the authenticated user.

Requires JWT

DELETE

/api/v1/contents/{id}

Delete a specific piece of content.

Requires JWT

💡 3. Design Decisions & Technical Overview

LLM Integration: Transition to Gemini Structured Output

Initial Approach (Hugging Face): We initially attempted to use the Hugging Face Inference API. This demonstrated modularity but led to constant 404/410 errors (Gone / Not Found) due to deprecated model paths and unstable service access on the free tier. This proved that relying on external free endpoints is risky for production deployment.

Current Solution (Gemini): To guarantee reliability and fulfill the assignment's requirement to use a Google AI service ("Google Vertex AI"), we switched the backend of llm_service.py to target the Gemini API.

How Gemini is Integrated:
The Python service makes a single asynchronous call to Gemini, asking it to perform both tasks (summarization and sentiment classification) and respond with a specific JSON schema. This approach ensures:

Reliability: The request is stable and less prone to path/model archiving issues.

Structured Output: We enforce the output format via Pydantic schema in the prompt, eliminating complex text parsing in the Python backend code.

Security: The API key is read securely from the application environment variables (.env).

Database & Structure

Database: MySQL via SQLAlchemy (Asynchronous ORM) is used for persistence. We successfully debugged and resolved the complex startup dependency that required the FastAPI container to wait for the MySQL container to be fully Healthy.

Authentication: Uses the OAuth2/JWT Bearer scheme with SHA256 hashing for strong security. We resolved the tricky Swagger UI implementation bug by correctly configuring the /login endpoint to accept Form Data, which the UI relies on for the Authorization modal.

☁️ 4. GCP Deployment Architecture (Theoretical)

Component

GCP Service

Role & Justification

Backend API (FastAPI)

Cloud Run

Serverless deployment of our Python container. Scales automatically and handles the I/O-bound task of waiting for the Gemini response efficiently without tying up resources.

Database (MySQL)

Cloud SQL

Fully managed database service (no manual patching or maintenance required). Provides a persistent and secure data layer separate from the stateless API layer.

Security & Traffic

API Gateway

Sits in front of Cloud Run to enforce external security policies (API key validation, rate limits) and manage traffic access.

CI/CD

GitHub Actions & Artifact Registry

GitHub Actions pushes the final Docker image to Artifact Registry, and a subsequent step triggers a deployment update to Cloud Run.