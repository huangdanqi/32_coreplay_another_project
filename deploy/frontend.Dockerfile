ARG NODE_IMAGE=node:18-alpine
FROM ${NODE_IMAGE} AS build

WORKDIR /app
COPY test_frontend/package*.json ./test_frontend/
WORKDIR /app/test_frontend
RUN npm ci || npm install
COPY test_frontend/ /app/test_frontend/

# Inject API base for build via Vite define
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

FROM nginx:alpine AS runtime
COPY --from=build /app/test_frontend/dist /usr/share/nginx/html
COPY deploy/nginx.default.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]


