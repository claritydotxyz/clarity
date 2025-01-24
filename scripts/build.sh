#!/bin/bash

# Exit on error
set -e

echo "Building Clarity application..."

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf dist build *.egg-info

# Run tests
echo "Running tests..."
poetry run pytest

# Build documentation
echo "Building documentation..."
poetry run mkdocs build

# Build application package
echo "Building application package..."
poetry build

# Build Docker image
if [ -f "docker/Dockerfile" ]; then
    echo "Building Docker image..."
    docker build -t clarity:latest -f docker/Dockerfile .
fi

echo "Build complete!"

# File: scripts/deploy.sh
#!/bin/bash

# Exit on error
set -e

# Check environment argument
if [ -z "$1" ]; then
    echo "Usage: deploy.sh <environment>"
    echo "Available environments: production, staging"
    exit 1
fi

ENVIRONMENT=$1
echo "Deploying Clarity to $ENVIRONMENT..."

# Load environment variables
if [ -f ".env.$ENVIRONMENT" ]; then
    source .env.$ENVIRONMENT
else
    echo "Error: Environment file .env.$ENVIRONMENT not found"
    exit 1
fi

# Validate deployment prerequisites
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "Error: AWS credentials not set"
    exit 1
fi

# Run database migrations
echo "Running database migrations..."
poetry run alembic upgrade head

# Build and push Docker image
echo "Building and pushing Docker image..."
docker build -t clarity:$ENVIRONMENT -f docker/Dockerfile .
docker tag clarity:$ENVIRONMENT $ECR_REPOSITORY:$ENVIRONMENT
docker push $ECR_REPOSITORY:$ENVIRONMENT

# Update ECS service
echo "Updating ECS service..."
aws ecs update-service \
    --cluster clarity-cluster \
    --service clarity-service \
    --force-new-deployment

echo "Deployment complete!"
