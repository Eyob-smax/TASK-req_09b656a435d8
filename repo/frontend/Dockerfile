FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --prefer-offline

COPY . .

RUN npm run build

# The built dist/ is used by the backend container via a shared volume.
# There is no standalone runtime stage; the FastAPI backend serves the static assets.
