# Clarity

Personal efficiency analysis engine that tracks resource allocation across time and finances using ML-driven insights.

### Core Features

- System-level activity tracking and resource monitoring
- ML pipeline for behavioral pattern analysis
- Financial data integration and processing
- Encrypted data storage with zero-knowledge architecture
- REST API with rate limiting and caching
- Real-time visualization dashboard

### Prerequisites

- Python 3.9+
- Poetry for dependency management
- PostgreSQL 13+
- Redis for caching

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/clarity.git
   cd clarity
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configurations
   ```

4. Initialize the database:
   ```bash
   poetry run alembic upgrade head
   ```

5. Start the development server:
   ```bash
   poetry run uvicorn main:app --reload
   ```

## Architecture

Clarity follows a modular architecture with the following main components:

- **API Layer**: FastAPI-based REST API
- **Core Engine**: Data collection and processing
- **ML Pipeline**: Pattern recognition and predictions
- **UI Layer**: React-based dashboard

### Quick Setup

```bash
git clone git@github.com:username/clarity.git
cd clarity

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
docker-compose up -d
python main.py
```

### Repository Structure

```
clarity/
├── api/
│   ├── __init__.py
│   ├── endpoints/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── insights.py
│   │   ├── patterns.py
│   │   └── users.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── cache.py
│   │   └── rate_limit.py
│   └── routers/
│       ├── __init__.py
│       ├── v1.py
│       └── v2.py
├── core/
│   ├── __init__.py
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── analyzer.py
│   │   ├── collector.py
│   │   └── processor.py
│   ├── patterns/
│   │   ├── __init__.py
│   │   ├── behavior.py
│   │   ├── financial.py
│   │   └── temporal.py
│   └── processors/
│       ├── __init__.py
│       ├── apps/
│       │   ├── __init__.py
│       │   ├── browser.py
│       │   ├── ide.py
│       │   ├── messaging.py
│       │   └── terminal.py
│       ├── system/
│       │   ├── __init__.py
│       │   ├── cpu.py
│       │   ├── memory.py
│       │   └── network.py
│       └── integrations/
│           ├── __init__.py
│           ├── calendar/
│           │   ├── __init__.py
│           │   ├── google.py
│           │   └── outlook.py
│           ├── financial/
│           │   ├── __init__.py
│           │   ├── plaid.py
│           │   └── stripe.py
│           └── productivity/
│               ├── __init__.py
│               ├── github.py
│               ├── jira.py
│               └── slack.py
├── ml/
│   ├── __init__.py
│   ├── features/
│   │   ├── __init__.py
│   │   ├── extractors.py
│   │   └── processors.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── attention.py
│   │   ├── clustering.py
│   │   └── sequence.py
│   ├── training/
│   │   ├── __init__.py
│   │   ├── dataloaders.py
│   │   └── trainers.py
│   └── inference/
│       ├── __init__.py
│       ├── pipeline.py
│       └── predictors.py
├── data/
│   ├── __init__.py
│   ├── collector/
│   │   ├── __init__.py
│   │   ├── hooks.py
│   │   └── watchers.py
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── encrypted.py
│   │   └── local.py
│   └── transforms/
│       ├── __init__.py
│       ├── cleaners.py
│       └── normalizers.py
├── ui/
│   ├── __init__.py
│   ├── assets/
│   │   ├── fonts/
│   │   ├── icons/
│   │   └── styles/
│   ├── components/
│   │   ├── __init__.py
│   │   ├── charts/
│   │   ├── insights/
│   │   └── shared/
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── dashboard/
│   │   ├── insights/
│   │   └── settings/
│   └── state/
│       ├── __init__.py
│       ├── actions.py
│       └── store.py
├── utils/
│   ├── __init__.py
│   ├── crypto/
│   │   ├── __init__.py
│   │   ├── encryption.py
│   │   └── hashing.py
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── logging.py
│   │   └── metrics.py
│   └── helpers/
│       ├── __init__.py
│       ├── dates.py
│       ├── formatting.py
│       └── validation.py
├── tests/
│   ├── integration/
│   │   ├── test_api.py
│   │   ├── test_collectors.py
│   │   └── test_storage.py
│   ├── unit/
│   │   ├── test_engine.py
│   │   ├── test_ml.py
│   │   └── test_processors.py
│   └── e2e/
│       ├── test_dashboard.py
│       └── test_workflow.py
├── scripts/
│   ├── setup.sh
│   ├── build.sh
│   └── deploy.sh
├── docs/
│   ├── api/
│   ├── architecture/
│   ├── deployment/
│   └── development/
├── migrations/
│   ├── __init__.py
│   └── versions/
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── nginx.conf
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   └── deploy.yml
│   └── ISSUE_TEMPLATE/
├── config/
│   ├── __init__.py
│   ├── development.py
│   ├── production.py
│   └── testing.py
├── alembic.ini
├── main.py
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── setup.py
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

### Development

```bash
# Run tests
pytest tests/

# Start dev server
python main.py --dev

# Build UI
cd ui && npm run build
```

### Components

- `api/`: REST endpoints and middleware
- `core/`: Business logic and processing engine
- `ml/`: Machine learning pipeline and models
- `data/`: Data collection and storage handlers
- `ui/`: Frontend dashboard
- `utils/`: Shared utilities and helpers

### License

MIT
