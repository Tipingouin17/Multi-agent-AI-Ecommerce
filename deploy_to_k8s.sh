#!/bin/bash

# deploy_to_k8s.sh
# Production-ready deployment script for Multi-Agent E-commerce to Kubernetes
# This script automates building, tagging, pushing Docker images, and applying
# the Kubernetes deployment with the correct image tag.

# --- Configuration ---
# Your Docker registry prefix (e.g., docker.io/myuser or myregistry.azurecr.io)
REGISTRY_PREFIX="your-registry"
# Base name for the project images
PROJECT_BASE_NAME="multi-agent-ecommerce"
# List of all components that need to be built and deployed
COMPONENTS=(
    "api"
    "order-agent"
    "inventory-agent"
    "marketplace-connector"
)

# --- Functions ---

# Function to display error and exit
error_exit() {
    echo "ERROR: $1" >&2
    exit 1
}

# Function to check if a command exists
check_command() {
    if ! command -v "$1" &> /dev/null
    then
        error_exit "$1 could not be found. Please install it."
    fi
}

# --- Main Script ---

echo "--- Starting Production Deployment Process ---"

# 1. Check Prerequisites
check_command "docker"
check_command "kubectl"
check_command "envsubst"

# 2. Generate a unique, immutable tag (e.g., based on Git SHA and timestamp)
# Fallback to timestamp if not in a Git repository
if [ -d .git ]; then
    GIT_COMMIT=$(git rev-parse --short HEAD)
    DEPLOYMENT_TAG="${GIT_COMMIT}-$(date +%Y%m%d%H%M%S)"
else
    echo "Warning: Not in a Git repository. Using timestamp for tag."
    DEPLOYMENT_TAG="manual-$(date +%Y%m%d%H%M%S)"
fi

echo "Generated Deployment Tag: ${DEPLOYMENT_TAG}"

# 3. Build, Tag, and Push Images
for COMPONENT in "${COMPONENTS[@]}"; do
    IMAGE_NAME="${REGISTRY_PREFIX}/${PROJECT_BASE_NAME}-${COMPONENT}"
    FULL_IMAGE_TAG="${IMAGE_NAME}:${DEPLOYMENT_TAG}"

    echo "--- Processing Component: ${COMPONENT} ---"

    # Build the image
    # Assuming Dockerfiles are named Dockerfile.<component> or similar,
    # or that the build context is the root and the Dockerfile is at the root.
    # For this project, we'll assume a standard build command from the root.
    # NOTE: You may need to adjust the -f flag if Dockerfiles are in subdirectories (e.g., agents/Dockerfile.order-agent)
    echo "Building ${FULL_IMAGE_TAG}..."
    docker build -t "${FULL_IMAGE_TAG}" . --no-cache || error_exit "Docker build failed for ${COMPONENT}"

    # Push the image
    echo "Pushing ${FULL_IMAGE_TAG} to registry..."
    docker push "${FULL_IMAGE_TAG}" || error_exit "Docker push failed for ${COMPONENT}"

    echo "Successfully built and pushed ${COMPONENT}."
done

# 4. Deploy to Kubernetes
echo "--- Deploying to Kubernetes Cluster ---"

# Set the TAG environment variable for envsubst
export TAG="${DEPLOYMENT_TAG}"

# Use envsubst to replace the placeholder in the YAML file with the actual tag
# and save it to a temporary file for deployment
TEMP_K8S_FILE="k8s/deployment.temp.yaml"
envsubst < "Multi-agent-AI-Ecommerce/k8s/deployment.yaml" > "${TEMP_K8S_FILE}" || error_exit "envsubst failed to process deployment.yaml"

echo "Applying Kubernetes configuration with tag ${DEPLOYMENT_TAG}..."
kubectl apply -f "${TEMP_K8S_FILE}" || error_exit "kubectl apply failed"

# Clean up temporary file
rm "${TEMP_K8S_FILE}"

echo "--- Deployment Successful! ---"
echo "New application version ${DEPLOYMENT_TAG} is rolling out."
echo "Check deployment status with: kubectl rollout status deployment/api-deployment -n ecommerce"

# Unset the environment variable
unset TAG
