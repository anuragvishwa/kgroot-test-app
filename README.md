# KGroot Test App

A sample microservice application for testing KGroot RCA (Root Cause Analysis) integration.

## Purpose

This repository is used to test:
- GitHub MCP integration with KGroot
- Issue correlation with Kubernetes incidents
- Code change analysis during RCA

## Services

- **api-server**: Main API service (Python/FastAPI)
- **payment-service**: Payment processing service
- **user-service**: User management service

## Kubernetes Deployment

```bash
kubectl apply -f kubernetes/
```

## Known Issues

Check the Issues tab for known bugs and incidents being tracked.
