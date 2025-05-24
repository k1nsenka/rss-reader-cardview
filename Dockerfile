# Dockerfile
FROM python:3.12-alpine

# Install system dependencies
RUN apk add --no-cache \
    tzdata \
    dcron \
    bash \
    curl

# Set timezone to JST
ENV TZ=Asia/Tokyo
RUN cp /usr/share/zoneinfo/Asia/Tokyo /etc/localtime && \
    echo "Asia/Tokyo" > /etc/timezone

# Create app directory
WORKDIR /app

# Install Python packages
RUN pip3 install --no-cache-dir \
    requests \
    jinja2

# Copy cron job configuration
# Schedule digest at 06:30 JST daily
RUN echo "30 6 * * * cd /app && /usr/bin/python3 /app/send_digest.py >> /var/log/cron.log 2>&1" > /etc/crontabs/root

# Create log file
RUN touch /var/log/cron.log

# Make scripts executable
RUN chmod +x /app/*.sh || true

# Default command - will be overridden by docker-compose
CMD ["sh", "-c", "crond -f -d 8 & tail -f /var/log/cron.log"]