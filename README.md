# TERRAVANT
### Intelligent Agriculture. Better Decisions. Sustainable Growth.

**TERRAVANT** is an AI-powered agricultural intelligence and decision-support platform designed to help farmers organize farm operations, understand field conditions, explore crop recommendations, estimate potential yields, and access agricultural insights through a unified digital workspace.

Built with a focus on practical agricultural workflows, machine-learning integration, and scalable software architecture, TERRAVANT aims to make data-driven agriculture more accessible.

<p align="center">
  <strong>Farm Management · Agricultural Intelligence · Machine Learning · Decision Support</strong>
</p>

---

## Overview

Agriculture involves complex decisions influenced by soil conditions, weather, crop selection, field activities, and seasonal factors. TERRAVANT brings several of these workflows together in one platform.

The system combines a modern web interface, a REST API, persistent data storage, and machine-learning components to provide a foundation for digital farm management and agricultural decision support.

TERRAVANT is initially designed around agricultural workflows relevant to Punjab, Pakistan, with an architecture that can be extended to additional regions and datasets.

## Core Capabilities

### Farm and Field Management
- Register and manage farms.
- Organize farms into individual fields.
- Maintain field-level information and records.
- Record soil tests and agricultural activities.
- Track farm information through a centralized workspace.

### Crop Recommendation
- Submit agricultural and environmental parameters.
- Generate crop recommendations using a machine-learning model.
- Review prediction results through the application.
- Maintain model metadata for traceability.

### Yield Prediction
- Submit relevant crop and environmental information.
- Estimate potential yield using a trained machine-learning model.
- Present prediction results through the dashboard.

### Plant Disease Detection
- Dedicated disease-detection workflow and backend inference integration.
- Structured support for disease classes and model metadata.
- Designed to accommodate a trained image-classification model.

**Current limitation:** A trained disease-detection model is not included in the current release. Disease inference is therefore unavailable until a compatible model is trained and deployed.

### Fertilizer Guidance
- Agricultural input guidance based on available field information.
- A foundation for future soil-aware fertilizer recommendations.
- Designed for integration with more comprehensive agronomic datasets.

**Current limitation:** Fertilizer guidance currently uses preliminary qualitative rules, not a scientifically validated fertilizer optimization model.

### Weather Integration
- Weather information through the Open-Meteo integration.
- Weather-related data to support agricultural decision-making.
- A foundation for future weather-aware recommendations.

### Notifications and Analytics
- Centralized notifications.
- Farm-related analytics and summary information.
- Administrative visibility into platform activity.

### Authentication and Administration
- User registration and authentication.
- Role-based access control.
- Protected application routes and API endpoints.
- Administrative user and model-management interfaces.
- Audit logging and session-management functionality.

---

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React, TypeScript, Vite |
| UI and Styling | Tailwind CSS |
| Data Visualization | Recharts |
| API | Python, FastAPI |
| Data Validation | Pydantic |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Database Migrations | Alembic |
| Authentication | JWT-based authentication and session management |
| Machine Learning | Scikit-learn, Joblib |
| Weather | Open-Meteo API |
| Testing | Pytest, Vitest |
| Code Quality | Ruff, TypeScript |
| Containerization | Docker, Docker Compose |
| CI | GitHub Actions |

---

## System Architecture

TERRAVANT follows a modular client-server architecture.

```text
                 TERRAVANT PLATFORM
                         |
          +--------------+--------------+
          |                             |
     React Frontend                FastAPI Backend
     TypeScript / Vite             REST API
          |                             |
          |                     +-------+-------+
          |                     |       |       |
          |                 Services  Security  ML
          |                     |       |       |
          |                     +-------+-------+
          |                             |
          |                       SQLAlchemy
          |                             |
          |                         PostgreSQL
          |
     User Interface
          |
     Farm Dashboard
     Field Management
     Predictions
     Notifications
     Administration
```

The backend separates API routing, data models, schemas, integrations, machine-learning components, and supporting services to keep the system maintainable and extensible.

---

## Project Structure

```text
TERRAVANT/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── backend/
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   ├── core/
│   │   ├── integrations/
│   │   ├── middleware/
│   │   ├── ml/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── types/
│   │   └── utils/
│   ├── Dockerfile
│   └── package.json
│
├── ml/
│   ├── artifacts/
│   ├── crop_recommendation/
│   ├── disease_detection/
│   ├── fertilizer_recommendation/
│   ├── shared/
│   └── yield_prediction/
│
├── datasets/
├── docs/
├── scripts/
├── tests/
├── docker-compose.yml
├── .env.example
├── Makefile
└── README.md
```

---

## Getting Started

### Prerequisites

Install the following tools before running TERRAVANT:

- Git
- Docker Desktop with Docker Compose
- Node.js 22 or compatible version
- Python 3.12 (for local backend development)

### 1. Clone the Repository

```bash
git clone https://github.com/ASAD1960/TERRAVANT.git
cd TERRAVANT
```

### 2. Configure Environment Variables

Create your local environment file from the example:

**Windows PowerShell**
```powershell
Copy-Item .env.example .env
```

**Linux / macOS**
```bash
cp .env.example .env
```

Update the environment variables before starting the application.

At minimum, configure:
- A strong, unique `SECRET_KEY`.
- A secure database password.
- The correct database connection settings.
- Appropriate frontend origins in `CORS_ORIGINS`.

Never commit `.env` files, passwords, API credentials, or production secrets.

### 3. Start with Docker Compose

From the project root:

```bash
docker compose up --build
```

Docker Compose starts the PostgreSQL database, FastAPI backend, and frontend services.

### 4. Access the Application

| Service | Address |
|---|---|
| Frontend | http://localhost:8080 |
| Backend API | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

The backend Docker startup process applies database migrations before launching the API.

### 5. Create an Administrator

For a new deployment, use the administrator creation script from the project environment. The script securely prompts for the administrator password.

See the project documentation and script instructions before running it.

---

## Machine Learning

Machine-learning components are organized independently under `ml/`.

| Component | Purpose | Current status |
|---|---|---|
| Crop Recommendation | Crop classification and recommendation | Demo model available |
| Yield Prediction | Yield estimation | Demo model available |
| Disease Detection | Plant disease image classification | Model not yet deployed |
| Fertilizer Guidance | Fertilizer decision support | Preliminary rule-based guidance |

### Model Training

Training scripts are provided for crop recommendation, yield prediction, and disease detection.

```bash
python ml/crop_recommendation/train.py
python ml/yield_prediction/train.py
```

For disease detection, install the additional dependencies and prepare a suitable labeled image dataset before training.

Refer to the documentation in `ml/` and `docs/` for model-specific requirements.

### Model Validation and Responsible Use

The currently included crop-recommendation and yield-prediction artifacts are trained using synthetic demonstration data.

They are intended to demonstrate model integration and application workflows, not to provide validated agricultural predictions.

Before real-world agricultural use, models require:
- Representative regional agricultural datasets.
- Data-quality checks and preprocessing.
- Independent validation against real observations.
- Appropriate performance metrics.
- Agronomic review and expert evaluation.
- Monitoring for changes in data and model performance.

Predictions should not be treated as guaranteed crop outcomes or professional agronomic advice.

---

## Testing and Quality Assurance

TERRAVANT includes automated backend and frontend tests.

### Backend

```bash
cd backend
python -m pytest -q
```

### Frontend

```bash
cd frontend
npm ci
npm run typecheck
npm test
npm run build
```

### Continuous Integration

The GitHub Actions workflow is configured to run automated checks, including backend tests, frontend validation, dependency checks, and Docker image builds.

---

## Security

Security is an important part of the platform's architecture.

Current security-related functionality includes:
- Password-based authentication.
- Protected API routes.
- Role-based authorization.
- Session management.
- Request validation.
- Rate limiting.
- Audit logging.
- Environment-based configuration.
- Database migrations.

**Deployment security:** A complete security review is required before production use. In particular, authentication-session behavior, refresh-token reuse events, deployment configuration, database access, and secret management must be reviewed and verified.

Do not use demonstration credentials or development configurations in production.

---

## Current Development Status

TERRAVANT has an implemented foundation covering its frontend, backend, database schema, authentication, farm workflows, integrations, and machine-learning interfaces.

| Area | Status |
|---|---|
| Frontend application | Implemented |
| Backend REST API | Implemented |
| Authentication | Implemented |
| Role-based access control | Implemented |
| Farm and field management | Implemented |
| Soil records and activities | Implemented |
| Notifications | Implemented |
| Weather integration | Implemented |
| Crop recommendation | Demo ML integration |
| Yield prediction | Demo ML integration |
| Fertilizer guidance | Preliminary rules |
| Disease detection | Model integration pending |
| Automated tests | Implemented |
| Docker configuration | Implemented |
| CI workflow | Configured |
| Production deployment | Not yet completed |

TERRAVANT is an evolving project. Features and validation status may change as development progresses.

---

## Roadmap

Planned areas of improvement include:

- [ ] Validate crop recommendation models using real regional datasets.
- [ ] Improve yield prediction accuracy through field observations.
- [ ] Train and integrate a validated plant disease-detection model.
- [ ] Develop soil-aware fertilizer recommendations.
- [ ] Expand weather-driven agricultural intelligence.
- [ ] Introduce more detailed farm analytics and reporting.
- [ ] Add regional crop calendars and agricultural guidance.
- [ ] Improve multilingual accessibility, including Urdu.
- [ ] Conduct comprehensive security and deployment reviews.
- [ ] Deploy a stable, publicly accessible demonstration.

---

## Documentation

Additional technical documentation is available in the `docs/` directory:

| Document | Description |
|---|---|
| `architecture.md` | System architecture |
| `deployment.md` | Deployment configuration and considerations |
| `ml-validation.md` | Machine-learning validation |
| `traceability.md` | Requirements and implementation traceability |

---

## Contributing

TERRAVANT is structured to support continued development and improvement.

Contributions, suggestions, and technical feedback are welcome.

For substantial changes:
1. Create a separate branch.
2. Keep changes focused and documented.
3. Add or update automated tests.
4. Verify backend and frontend checks.
5. Submit a pull request with a clear description.

---

## Author

**Asad Yar**

Computer Science Graduate | Software Developer | AI & Machine Learning Enthusiast

- GitHub: [@ASAD1960](https://github.com/ASAD1960)
- LinkedIn: [Asad Yar](https://www.linkedin.com/in/asad-yar-692862339/)

---

## License

No open-source license has been declared yet. All rights are reserved by the author unless a license is added to this repository.

---

<p align="center">
  <strong>TERRAVANT</strong><br/>
  Intelligent Agriculture. Better Decisions. Sustainable Growth.
  <br/><br/>
  Built with purpose by Asad Yar.
</p>