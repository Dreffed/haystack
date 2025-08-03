FROM nginx:alpine

# Copy static files
COPY docker/frontend/ /usr/share/nginx/html/

# Copy nginx configuration
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Create health check endpoint
RUN echo '<!DOCTYPE html><html><head><title>Health Check</title></head><body>OK</body></html>' > /usr/share/nginx/html/health

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Install curl for health checks
RUN apk add --no-cache curl

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]