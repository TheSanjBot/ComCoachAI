FROM node:22-alpine AS deps

WORKDIR /app/frontend

COPY frontend/package.json ./
COPY frontend/package-lock.json* ./
RUN npm install

COPY frontend ./
RUN npm run build

ENV NODE_ENV=production

CMD ["npm", "run", "start", "--", "--hostname", "0.0.0.0", "--port", "3000"]
