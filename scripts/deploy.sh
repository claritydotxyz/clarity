#!/bin/bash
set -e

# Configuration
ENVIRONMENT=$1
APP_NAME="clarity"
DOCKER_REGISTRY="registry.example.com"
NAMESPACE="clarity-${ENVIRONMENT}"

# Check environment argument
if [ -z "$ENVIRONMENT" ]; then
    echo "Usage: deploy.sh <environment>"
    echo "Available environments: production, staging"
    exit 1
fi

# Load environment variables
if [ -f ".env.${ENVIRONMENT}" ]; then
    source ".env.${ENVIRONMENT}"
else
    echo "Error: Environment file .env.${ENVIRONMENT} not found"
    exit 1
fi

echo "Deploying ${APP_NAME} to ${ENVIRONMENT}..."

# Run database migrations
echo "Running database migrations..."
poetry run alembic upgrade head

# Build Docker image
echo "Building Docker image..."
docker build -t ${APP_NAME}:${ENVIRONMENT} -f docker/Dockerfile .

# Tag and push to registry
echo "Pushing to registry..."
docker tag ${APP_NAME}:${ENVIRONMENT} ${DOCKER_REGISTRY}/${APP_NAME}:${ENVIRONMENT}
docker push ${DOCKER_REGISTRY}/${APP_NAME}:${ENVIRONMENT}

# Deploy to Kubernetes
echo "Deploying to Kubernetes..."
kubectl config use-context ${ENVIRONMENT}

# Update deployments
kubectl -n ${NAMESPACE} set image deployment/${APP_NAME} \
    ${APP_NAME}=${DOCKER_REGISTRY}/${APP_NAME}:${ENVIRONMENT}

# Wait for rollout
kubectl -n ${NAMESPACE} rollout status deployment/${APP_NAME}

# Run post-deploy tasks
echo "Running post-deploy tasks..."
./scripts/post-deploy.sh ${ENVIRONMENT}

echo "Deployment completed successfully!"
