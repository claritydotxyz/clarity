# Clarity

Personal efficiency analysis engine that tracks resource allocation across time and finances using ML-driven insights.

### Core Features

- System-level activity tracking and resource monitoring
- ML pipeline for behavioral pattern analysis
- Financial data integration and processing
- Encrypted data storage with zero-knowledge architecture
- REST API with rate limiting and caching
- Real-time visualization dashboard

### Requirements

- Python >= 3.9
- PostgreSQL >= 13
- Redis >= 6
- Docker + Compose
- Node.js >= 18

### Quick Setup

```bash
git clone git@github.com:claritydotxyz/clarity.git
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
│   ├── init.py
│   ├── endpoints/
│   │   ├── init.py
│   │   ├── auth.py
│   │   ├── insights.py
│   │   ├── patterns.py
│   │   └── users.py
│   ├── middleware/
│   │   ├── init.py
│   │   ├── auth.py
│   │   ├── cache.py
│   │   └── rate_limit.py
│   └── routers/
│       ├── init.py
│       ├── v1.py
│       └── v2.py
├── core/
│   ├── init.py
│   ├── engine/
│   │   ├── init.py
│   │   ├── analyzer.py
│   │   ├── collector.py
│   │   └── processor.py
│   ├── patterns/
│   │   ├── init.py
│   │   ├── behavior.py
│   │   ├── financial.py
│   │   └── temporal.py
│   └── processors/
│       ├── init.py
│       ├── apps/
│       │   ├── init.py
│       │   ├── browser.py
│       │   ├── ide.py
│       │   ├── messaging.py
│       │   └── terminal.py
│       ├── system/
│       │   ├── init.py
│       │   ├── cpu.py
│       │   ├── memory.py
│       │   └── network.py
│       └── integrations/
│           ├── init.py
│           ├── calendar/
│           │   ├── init.py
│           │   ├── google.py
│           │   └── outlook.py
│           ├── financial/
│           │   ├── init.py
│           │   ├── plaid.py
│           │   └── stripe.py
│           └── productivity/
│               ├── init.py
│               ├── github.py
│               ├── jira.py
│               └── slack.py
├── ml/
│   ├── init.py
│   ├── features/
│   │   ├── init.py
│   │   ├── extractors.py
│   │   └── processors.py
│   ├── models/
│   │   ├── init.py
│   │   ├── attention.py
│   │   ├── clustering.py
│   │   └── sequence.py
│   ├── training/
│   │   ├── init.py
│   │   ├── dataloaders.py
│   │   └── trainers.py
│   └── inference/
│       ├── init.py
│       ├── pipeline.py
│       └── predictors.py
├── data/
│   ├── init.py
│   ├── collector/
│   │   ├── init.py
│   │   ├── hooks.py
│   │   └── watchers.py
│   ├── storage/
│   │   ├── init.py
│   │   ├── encrypted.py
│   │   └── local.py
│   └── transforms/
│       ├── init.py
│       ├── cleaners.py
│       └── normalizers.py
├── ui/
│   ├── init.py
│   ├── assets/
│   │   ├── fonts/
│   │   ├── icons/
│   │   └── styles/
│   ├── components/
│   │   ├── init.py
│   │   ├── charts/
│   │   ├── insights/
│   │   └── shared/
│   ├── pages/
│   │   ├── init.py
│   │   ├── dashboard/
│   │   ├── insights/
│   │   └── settings/
│   └── state/
│       ├── init.py
│       ├── actions.py
│       └── store.py
├── utils/
│   ├── init.py
│   ├── crypto/
│   │   ├── init.py
│   │   ├── encryption.py
│   │   └── hashing.py
│   ├── monitoring/
│   │   ├── init.py
│   │   ├── logging.py
│   │   └── metrics.py
│   └── helpers/
│       ├── init.py
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
├── migrations/
│   ├── init.py
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
│   ├── init.py
│   ├── development.py
│   ├── production.py
│   └── testing.py
├── alembic.ini
├── main.py
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── setup.py
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
