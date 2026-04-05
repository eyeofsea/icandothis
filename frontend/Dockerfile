FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json* pnpm-lock.yaml* ./
RUN corepack enable && pnpm install --frozen-lockfile 2>/dev/null || npm ci

COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_API_URL=https://api.vints.ai
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN mkdir -p ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
