FROM node:lts-alpine AS builder
WORKDIR /app
COPY contrib/front/package*.json ./
RUN npm install
COPY contrib/front/ .
RUN npm run build

FROM nginx:1.27.3
COPY --from=builder /app/dist /usr/share/nginx/html
