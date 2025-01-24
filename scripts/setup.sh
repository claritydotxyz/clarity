#!/bin/bash

# Exit on error
set -e

echo "Setting up Clarity development environment..."

# Check Python version
python_version=$(python3 --version)
if [[ $python_version != *"3.9"* ]]; then
    echo "Error: Python 3.9 is required"
    exit 1
fi

# Install Poetry
if ! command -v poetry &> /dev/null; then
    echo "Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
fi

# Install dependencies
echo "Installing project dependencies..."
poetry install

# Set up pre-commit hooks
echo "Setting up pre-commit hooks..."
poetry run pre-commit install

# Initialize development database
echo "Setting up development database..."
if command -v docker &> /dev/null; then
    docker-compose -f docker/docker-compose.yml up -d db
    sleep 5  # Wait for database to start
else
    echo "Warning: Docker not found, skipping database setup"
fi

# Run migrations
echo "Running database migrations..."
poetry run alembic upgrade head

# Generate development SSL certificates
echo "Generating development SSL certificates..."
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/dev.key -out ssl/dev.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

echo "Setup complete! You can now start the development server with:"
echo "poetry run uvicorn clarity.main:app --reload"
