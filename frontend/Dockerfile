# Placeholder Dockerfile for the Next.js frontend.
# See TASKS.md T52.
#
# TODO:
# - multi-stage build producing a Next.js standalone output
# - exclude dev-only dependencies from the final image layer
# - backend API URL must be a runtime env var, not a build-time constant

FROM node:20-alpine

WORKDIR /app

COPY package.json .
# RUN npm install

COPY . .

# CMD ["npm", "start"]
