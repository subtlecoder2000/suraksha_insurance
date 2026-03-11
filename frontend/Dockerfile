# Stage 1: Build React/Vite app
FROM node:18-slim AS build

WORKDIR /app

# Copy package.json and package-lock.json (if exists)
# Note: we are currently in frontend/ when we run this build context
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source
COPY . .

# Build for production
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Run nginx
CMD ["nginx", "-g", "daemon off;"]
