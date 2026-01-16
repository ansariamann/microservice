# Production Deployment Guide

This guide covers deploying the Task Management System in production environments with security, monitoring, and scalability considerations.

## Prerequisites

### Infrastructure Requirements

- **Server**: Linux server with 4GB+ RAM, 20GB+ storage
- **Docker**: Docker Engine 20.10+ and Docker Compose 2.0+
- **Network**: Ports 80, 443 available for web traffic
- **Domain**: Optional but recommended for SSL/TLS

### Security Requirements

- **Firewall**: Configure to allow only necessary ports
- **SSL/TLS**: Certificate for HTTPS (Let's Encrypt recommended)
- **Secrets Management**: Secure storage for environment variables
- **Backup Strategy**: Regular database backups

## Production Setup

### 1. Server Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install additional tools
sudo apt install -y git curl htop
```

### 2. Application Deployment

```bash
# Clone repository
git clone <repository-url>
cd microservices-task-management

# Run initial setup
./scripts/manage.sh setup
```

### 3. Production Configuration

Create and configure the production environment file:

```bash
cp .env.prod.template .env.prod
nano .env.prod
```

**Critical Production Settings:**

```bash
# Security - Use strong, unique values
JWT_SECRET=REPLACE-WITH-STRONG-RANDOM-64-CHARACTER-STRING
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Database Configuration - Use secure passwords
POSTGRES_DB=userdb_prod
POSTGRES_USER=taskuser
POSTGRES_PASSWORD=REPLACE-WITH-SECURE-PASSWORD-32-CHARS-MIN
POSTGRES_PORT=5432

MONGODB_DATABASE=taskdb_prod
MONGODB_PORT=27017

# Production Mode
DEBUG=false
LOG_LEVEL=INFO
LOG_FORMAT=json

# CORS Configuration - Restrict to your domain
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Frontend Configuration - Use your domain
REACT_APP_API_BASE_URL=https://yourdomain.com
REACT_APP_USER_SERVICE_URL=https://yourdomain.com
REACT_APP_TASK_SERVICE_URL=https://yourdomain.com
REACT_APP_NOTIFICATION_SERVICE_URL=https://yourdomain.com

# Resource Limits
USER_SERVICE_MEMORY_LIMIT=512m
TASK_SERVICE_MEMORY_LIMIT=512m
NOTIFICATION_SERVICE_MEMORY_LIMIT=256m
FRONTEND_MEMORY_LIMIT=256m

# Database Limits
POSTGRES_MEMORY_LIMIT=1g
MONGODB_MEMORY_LIMIT=1g
```

### 4. SSL/TLS Configuration

**Option A: Let's Encrypt (Recommended)**

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Update nginx configuration to use certificates
# Certificates will be in /etc/letsencrypt/live/yourdomain.com/
```

**Option B: Custom Certificate**

Place your certificate files in `nginx/ssl/`:

- `nginx/ssl/cert.pem` - Certificate file
- `nginx/ssl/key.pem` - Private key file

### 5. Start Production Environment

```bash
# Start production environment
./scripts/manage.sh prod

# Start with monitoring
./scripts/manage.sh prod --monitoring

# Verify deployment
./scripts/manage.sh health
```

## Production Architecture

### Container Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Production Environment                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Nginx     │  │  Frontend   │  │  Frontend   │         │
│  │  (Gateway)  │  │ (Replica 1) │  │ (Replica 2) │         │
│  │             │  │             │  │             │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │User Service │  │User Service │  │Task Service │         │
│  │ (Replica 1) │  │ (Replica 2) │  │ (Replica 1) │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │Task Service │  │Notification │  │Notification │         │
│  │ (Replica 2) │  │   Service   │  │   Service   │         │
│  │             │  │ (Replica 1) │  │ (Replica 2) │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ PostgreSQL  │  │  MongoDB    │  │   SQLite    │         │
│  │ (User Data) │  │(Task Data)  │  │(Notifications)       │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### Service Scaling

Production configuration includes:

- **2 replicas** of each backend service
- **2 replicas** of the frontend
- **Load balancing** via Nginx
- **Health checks** for all services
- **Automatic restart** on failure

### Resource Allocation

**Service Limits:**

- User Service: 0.5 CPU, 512MB RAM per replica
- Task Service: 0.5 CPU, 512MB RAM per replica
- Notification Service: 0.5 CPU, 256MB RAM per replica
- Frontend: 0.5 CPU, 256MB RAM per replica
- Nginx: 0.5 CPU, 256MB RAM

**Database Limits:**

- PostgreSQL: 1 CPU, 1GB RAM
- MongoDB: 1 CPU, 1GB RAM

## Security Configuration

### Network Security

**Firewall Rules:**

```bash
# Allow SSH (adjust port as needed)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

**Docker Network Isolation:**

- Services communicate via internal Docker networks
- Only Nginx gateway exposes ports to host
- Database ports not exposed externally

### Application Security

**JWT Configuration:**

- Strong secret key (64+ characters)
- Short token expiration (24 hours)
- Secure token storage in frontend

**Database Security:**

- Strong passwords for all databases
- No default credentials
- Connection encryption where supported

**Input Validation:**

- All user inputs validated and sanitized
- SQL injection prevention via ORM
- XSS protection in frontend

### HTTPS Configuration

**Nginx SSL Configuration:**

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
}
```

## Monitoring and Logging

### Monitoring Stack

Start with monitoring enabled:

```bash
./scripts/manage.sh prod --monitoring
```

**Monitoring Services:**

- **Prometheus** (http://yourdomain.com:9090) - Metrics collection
- **Grafana** (http://yourdomain.com:3001) - Visualization
- **cAdvisor** (http://yourdomain.com:8080) - Container metrics
- **Node Exporter** (http://yourdomain.com:9100) - System metrics

**Default Credentials:**

- Grafana: admin/admin123 (change immediately)

### Log Management

**Log Configuration:**

- Structured JSON logging in production
- Log rotation (10MB files, 5 file retention)
- Centralized logging via Fluentd

**Log Locations:**

```bash
# Application logs
docker-compose logs -f user-service
docker-compose logs -f task-service
docker-compose logs -f notification-service

# Nginx logs
docker-compose logs -f nginx

# System logs
journalctl -u docker
```

### Health Monitoring

**Health Check Endpoints:**

- Application: `https://yourdomain.com/health`
- Individual services: `https://yourdomain.com/api/v1/health`
- Nginx status: `https://yourdomain.com/nginx_status`

**Automated Monitoring:**

```bash
# Create health check script
cat > /usr/local/bin/health-check.sh << 'EOF'
#!/bin/bash
curl -f https://yourdomain.com/health || exit 1
EOF

chmod +x /usr/local/bin/health-check.sh

# Add to crontab for regular checks
echo "*/5 * * * * /usr/local/bin/health-check.sh" | crontab -
```

## Backup and Recovery

### Database Backup

**PostgreSQL Backup:**

```bash
# Create backup script
cat > /usr/local/bin/backup-postgres.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

docker exec task-mgmt-user-db-prod pg_dump -U taskuser userdb_prod > $BACKUP_DIR/userdb_$DATE.sql

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
EOF

chmod +x /usr/local/bin/backup-postgres.sh

# Schedule daily backups
echo "0 2 * * * /usr/local/bin/backup-postgres.sh" | crontab -
```

**MongoDB Backup:**

```bash
# Create backup script
cat > /usr/local/bin/backup-mongodb.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups/mongodb"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

docker exec task-mgmt-task-db-prod mongodump --db taskdb_prod --out /tmp/backup
docker cp task-mgmt-task-db-prod:/tmp/backup $BACKUP_DIR/mongodb_$DATE

# Keep only last 7 days
find $BACKUP_DIR -name "mongodb_*" -mtime +7 -exec rm -rf {} \;
EOF

chmod +x /usr/local/bin/backup-mongodb.sh
```

### Application Backup

**Configuration Backup:**

```bash
# Backup environment and configuration files
tar -czf /opt/backups/config_$(date +%Y%m%d).tar.gz \
  .env.prod \
  nginx/conf.d/ \
  docker-compose.prod.yml
```

### Recovery Procedures

**Service Recovery:**

```bash
# Restart failed service
docker-compose restart user-service

# Full system restart
./scripts/manage.sh stop prod
./scripts/manage.sh prod

# Restore from backup
docker exec -i task-mgmt-user-db-prod psql -U taskuser userdb_prod < backup.sql
```

## Maintenance

### Regular Maintenance Tasks

**Weekly:**

- Check disk space usage
- Review application logs for errors
- Verify backup integrity
- Update security patches

**Monthly:**

- Update Docker images
- Review monitoring metrics
- Clean up old logs and backups
- Security audit

### Update Procedures

**Application Updates:**

```bash
# Pull latest code
git pull origin main

# Backup current state
./scripts/manage.sh stop prod
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache

# Deploy update
./scripts/manage.sh prod

# Verify deployment
./scripts/manage.sh health
```

**Security Updates:**

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker
sudo apt update && sudo apt install docker-ce docker-ce-cli containerd.io

# Restart services
./scripts/manage.sh stop prod
./scripts/manage.sh prod
```

## Troubleshooting

### Common Production Issues

**High Memory Usage:**

```bash
# Check container memory usage
docker stats

# Check system memory
free -h

# Restart memory-intensive services
docker-compose restart task-service
```

**Database Connection Issues:**

```bash
# Check database container status
docker-compose ps

# Check database logs
docker-compose logs postgres
docker-compose logs mongodb

# Test database connectivity
docker exec task-mgmt-user-db-prod pg_isready
```

**SSL Certificate Issues:**

```bash
# Check certificate expiration
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/cert.pem -text -noout | grep "Not After"

# Renew Let's Encrypt certificate
sudo certbot renew

# Restart nginx
docker-compose restart nginx
```

### Performance Optimization

**Database Optimization:**

- Monitor query performance
- Add database indexes as needed
- Configure connection pooling
- Regular database maintenance

**Application Optimization:**

- Monitor response times
- Optimize slow API endpoints
- Implement caching where appropriate
- Scale services based on load

**Infrastructure Optimization:**

- Monitor resource usage
- Adjust container resource limits
- Consider horizontal scaling
- Optimize Docker images

## Scaling Considerations

### Horizontal Scaling

**Service Scaling:**

```yaml
# In docker-compose.prod.yml
user-service:
  deploy:
    replicas: 4 # Increase replicas
    resources:
      limits:
        cpus: "0.5"
        memory: 512M
```

**Database Scaling:**

- PostgreSQL: Consider read replicas
- MongoDB: Consider sharding
- SQLite: Migrate to PostgreSQL for notifications

### Load Balancing

**Nginx Configuration:**

```nginx
upstream user_service {
    server user-service-1:8001;
    server user-service-2:8001;
    server user-service-3:8001;
    server user-service-4:8001;
}
```

### Infrastructure Scaling

**Multi-Server Deployment:**

- Use Docker Swarm or Kubernetes
- Implement service discovery
- Configure shared storage
- Set up load balancer

## Security Checklist

- [ ] Strong JWT secret configured
- [ ] Database passwords changed from defaults
- [ ] HTTPS enabled with valid certificate
- [ ] Firewall configured to allow only necessary ports
- [ ] CORS origins restricted to production domains
- [ ] Debug mode disabled
- [ ] Log level set to INFO or WARNING
- [ ] Security headers configured in Nginx
- [ ] Regular security updates scheduled
- [ ] Backup and recovery procedures tested

## Support and Maintenance

For ongoing support:

1. Monitor application logs regularly
2. Set up alerting for critical issues
3. Keep documentation updated
4. Plan for regular maintenance windows
5. Have rollback procedures ready

For additional help, refer to:

- [API Documentation](../user-service/API_DOCUMENTATION.md)
- [Development Setup](DEVELOPMENT_SETUP.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
