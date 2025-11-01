FROM node:20-slim

WORKDIR /app

COPY package.json package-lock.json* pnpm-lock.yaml* yarn.lock* ./
RUN npm install --no-audit --no-fund || true

COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev", "--", "-p", "3000", "-H", "0.0.0.0"]
