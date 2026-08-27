FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./

RUN corepack enable
RUN corepack prepare pnpm@11.18.0 --activate

RUN pnpm install --frozen-lockfile

COPY . .

RUN pnpm build


FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]