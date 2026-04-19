FROM node:20-bookworm-slim AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --prefer-offline
RUN npx playwright install --with-deps chromium

COPY . .

RUN npm run build

# The built dist/ is used by the backend container via a shared volume.
# There is no standalone runtime stage; the FastAPI backend serves the static assets.
