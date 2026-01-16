# Troubleshooting Guide

This guide helps diagnose and resolve common issues with the Task Management System.

## Quick Diagnostics

### System Health Check

```bash
# Check overall system health
./scripts/manage.sh health

# Check container status
./scripts/manage.sh status

# View recent logs
./scripts/manage.sh logs
```

### Service Availability

```bash
# Test individual services
curl http://localhost:8001/health  # User Service
curl http://localhost:8002/health  # Task Service
curl http://localhost:8003/health  # Notification Service
curl http://localhost:3000         # Frontend
```

## Common Issues

### 1. Services Won't Start

**Symptoms:**

- Containers exit immediately
- "Connection refused" errors
- Services not responding to health checks

**Diagnosis:**

```bash
# Check container status
docker-compose ps

# View container logs
docker-compose logs user-service
docker-compose logs task-service
docker-compose logs notification-service

# Check for port conflicts
netstat -tulpn | grep :8001
lsof -i :8001
```

**Solutions:**

**Port Conflicts:**

```bash
# Kill process using the port
kill -9 $(lsof -t -i:8001)

# Or change port in .env file
USER_SERVICE_PORT=8011
```

**Environment Variables:**

```bash
# Verify .env file exists and is properly formatted
cat .env

# Check for missing required variables
grep -E "JWT_SECRET|POSTGRES_PASSWORD" .env
```

**Docker Issues:**

```bash
# Rebuild containers
docker-compose build --no-cache

# Clean up Docker resources
docker system prune -f

# Reset volumes (WARNING: deletes data)
docker-compose down -v
```

### 2. Database Connection Issues

**Symptoms:**

- "Connection to database failed" errors
- Services start but can't access data
- Database-related 500 errors

**Diagnosis:**

```bash
# Check database container status
docker-compose ps | grep -E "(postgres|mongo|sqlite)"

# Check database logs
docker-compose logs user-db
docker-compose logs task-db

# Test database connectivity
docker exec task-mgmt-user-db pg_isready -U user
docker exec task-mgmt-task-db mongosh --eval "db.runCommand('ping')"
```

**Solutions:**

**PostgreSQL Issues:**

```bash
# Connect to database manually
docker exec -it task-mgmt-user-db psql -U user -d userdb

# Check database exists
\l

# Check tables exist
\dt

# Reset database (WARNING: deletes data)
docker-compose down
docker volume rm task-mgmt_user_db_data
docker-compose up -d user-db
```

**MongoDB Issues:**

```bash
# Connect to MongoDB
docker exec -it task-mgmt-task-db mongosh taskdb

# Check collections
show collections

# Check connection
db.runCommand('ping')

# Reset MongoDB (WARNING: deletes data)
docker-compose down
docker volume rm task-mgmt_task_db_data
docker-compose up -d task-db
```

**SQLite Issues:**

```bash
# Check SQLite file exists
docker exec task-mgmt-notification-service ls -la /app/notifications.db

# Connect to SQLite
docker exec -it task-mgmt-notification-service sqlite3 /app/notifications.db

# Check tables
.tables

# Reset SQLite (WARNING: deletes data)
docker exec task-mgmt-notification-service rm -f /app/notifications.db
docker-compose restart notification-service
```

### 3. Authentication Issues

**Symptoms:**

- "Invalid or expired token" errors
- Users can't log in
- 401 Unauthorized responses

**Diagnosis:**

```bash
# Check JWT secret consistency
grep JWT_SECRET .env

# Test login endpoint
curl -X POST http://localhost:8001/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass"}'

# Check user exists in database
docker exec -it task-mgmt-user-db psql -U user -d userdb -c "SELECT * FROM users;"
```

**Solutions:**

**JWT Secret Mismatch:**

```bash
# Ensure all services use same JWT_SECRET
grep JWT_SECRET .env

# Update all services with same secret
JWT_SECRET=your-consistent-secret-key
```

**User Registration Issues:**

```bash
# Create test user
curl -X POST http://localhost:8001/api/v1/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "name": "Test User"
  }'
```

**Token Expiration:**

```bash
# Check token expiration setting
grep JWT_EXPIRATION_HOURS .env

# Increase expiration time if needed
JWT_EXPIRATION_HOURS=24
```

### 4. Service Communication Issues

**Symptoms:**

- Tasks created but no notifications
- Services can't reach each other
- Intermittent failures

**Diagnosis:**

```bash
# Check Docker network
docker network ls
docker network inspect task-mgmt_default

# Test service-to-service communication
docker exec task-mgmt-task-service curl http://notification-service:8003/health

# Check service discovery
docker exec task-mgmt-task-service nslookup notification-service
```

**Solutions:**

**Network Issues:**

```bash
# Recreate Docker network
docker-compose down
docker network prune
docker-compose up -d
```

**Service URLs:**

```bash
# Verify internal service URLs in code
grep -r "notification-service" task-service/
grep -r "user-service" task-service/

# Check environment variables
docker exec task-mgmt-task-service env | grep SERVICE_URL
```

### 5. Frontend Issues

**Symptoms:**

- White screen or loading forever
- API calls failing
- CORS errors in browser console

**Diagnosis:**

```bash
# Check frontend container
docker-compose logs frontend

# Check nginx configuration
docker exec task-mgmt-nginx nginx -t

# Test API endpoints from browser network tab
# Check browser console for errors
```

**Solutions:**

**CORS Issues:**

```bash
# Update CORS origins in .env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Restart services
docker-compose restart user-service task-service notification-service
```

**API URL Configuration:**

```bash
# Check frontend environment variables
grep REACT_APP .env

# Verify API base URL
REACT_APP_API_BASE_URL=http://localhost:8080
```

**Build Issues:**

```bash
# Rebuild frontend
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### 6. Performance Issues

**Symptoms:**

- Slow response times
- High CPU or memory usage
- Timeouts

**Diagnosis:**

```bash
# Check resource usage
docker stats

# Check system resources
htop
free -h
df -h

# Check service response times
time curl http://localhost:8001/health
```

**Solutions:**

**Memory Issues:**

```bash
# Increase Docker memory limit
# In Docker Desktop: Settings > Resources > Memory

# Restart services
docker-compose restart
```

**Database Performance:**

```bash
# Check database performance
docker exec task-mgmt-user-db psql -U user -d userdb -c "SELECT * FROM pg_stat_activity;"

# Add database indexes if needed
# Check slow query logs
```

**Container Limits:**

```bash
# Check container resource limits in docker-compose.yml
# Increase limits if needed:
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '1.0'
```

## Environment-Specific Issues

### Development Environment

**Hot Reload Not Working:**

```bash
# Check volume mounts
docker-compose config | grep volumes

# Verify file changes are detected
docker-compose logs frontend | grep -i reload
```

**Database Data Persistence:**

```bash
# Check volume mounts
docker volume ls | grep task-mgmt

# Backup data before cleanup
docker exec task-mgmt-user-db pg_dump -U user userdb > backup.sql
```

### Production Environment

**SSL Certificate Issues:**

```bash
# Check certificate validity
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/cert.pem -text -noout

# Renew certificate
sudo certbot renew

# Check nginx SSL configuration
docker exec task-mgmt-nginx nginx -t
```

**Load Balancing Issues:**

```bash
# Check upstream servers
docker exec task-mgmt-nginx cat /etc/nginx/conf.d/default.conf

# Test individual service instances
curl -H "Host: yourdomain.com" http://user-service-1:8001/health
curl -H "Host: yourdomain.com" http://user-service-2:8001/health
```

## Monitoring and Debugging

### Log Analysis

**Structured Log Searching:**

```bash
# Search for errors
docker-compose logs | grep -i error

# Search for specific user actions
docker-compose logs | grep "user_id.*123"

# Search for API endpoint calls
docker-compose logs | grep "POST /api/v1/tasks"

# Filter by service
docker-compose logs user-service | grep -i error
```

**Log Levels:**

```bash
# Increase log verbosity for debugging
LOG_LEVEL=DEBUG

# Restart services to apply
docker-compose restart
```

### Performance Monitoring

**Resource Monitoring:**

```bash
# Real-time container stats
docker stats

# Historical resource usage
docker exec task-mgmt-prometheus curl http://localhost:9090/api/v1/query?query=container_memory_usage_bytes

# Service response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8001/health
```

**Database Monitoring:**

```bash
# PostgreSQL performance
docker exec task-mgmt-user-db psql -U user -d userdb -c "
  SELECT query, calls, total_time, mean_time
  FROM pg_stat_statements
  ORDER BY total_time DESC
  LIMIT 10;"

# MongoDB performance
docker exec task-mgmt-task-db mongosh taskdb --eval "db.runCommand({serverStatus: 1})"
```

### Network Debugging

**Service Connectivity:**

```bash
# Test internal network connectivity
docker exec task-mgmt-user-service ping task-service
docker exec task-mgmt-task-service ping notification-service

# Check DNS resolution
docker exec task-mgmt-user-service nslookup task-service
```

**Port Accessibility:**

```bash
# Check if ports are accessible
telnet localhost 8001
nc -zv localhost 8001

# Check from inside containers
docker exec task-mgmt-user-service nc -zv task-service 8002
```

## Recovery Procedures

### Service Recovery

**Individual Service Restart:**

```bash
# Restart specific service
docker-compose restart user-service

# Force recreate service
docker-compose up -d --force-recreate user-service
```

**Full System Recovery:**

```bash
# Stop all services
./scripts/manage.sh stop

# Clean up resources
docker system prune -f

# Restart system
./scripts/manage.sh dev  # or prod
```

### Data Recovery

**Database Recovery:**

```bash
# Restore PostgreSQL from backup
docker exec -i task-mgmt-user-db psql -U user -d userdb < backup.sql

# Restore MongoDB from backup
docker exec task-mgmt-task-db mongorestore --db taskdb /backup/taskdb

# Reset notification database
docker exec task-mgmt-notification-service rm -f /app/notifications.db
docker-compose restart notification-service
```

### Configuration Recovery

**Reset Environment:**

```bash
# Backup current config
cp .env .env.backup

# Reset to defaults
./scripts/manage.sh setup

# Restore custom settings
diff .env.backup .env
```

## Getting Help

### Information to Collect

When reporting issues, include:

1. **System Information:**

   ```bash
   uname -a
   docker --version
   docker-compose --version
   ```

2. **Service Status:**

   ```bash
   ./scripts/manage.sh status
   ./scripts/manage.sh health
   ```

3. **Recent Logs:**

   ```bash
   docker-compose logs --tail=100 > logs.txt
   ```

4. **Configuration:**
   ```bash
   # Remove sensitive data before sharing
   cat .env | sed 's/PASSWORD=.*/PASSWORD=***/' > config.txt
   ```

### Debug Mode

**Enable Debug Logging:**

```bash
# In .env file
DEBUG=true
LOG_LEVEL=DEBUG

# Restart services
docker-compose restart
```

**Verbose Docker Output:**

```bash
# Run with verbose output
docker-compose --verbose up
```

### Community Resources

- Check GitHub issues for similar problems
- Review API documentation for endpoint details
- Consult Docker and service-specific documentation
- Use browser developer tools for frontend issues

## Prevention

### Regular Maintenance

- Monitor disk space and clean up logs
- Keep Docker images updated
- Regular backup testing
- Monitor resource usage trends
- Review and rotate secrets

### Best Practices

- Use health checks in production
- Implement proper logging
- Monitor key metrics
- Have rollback procedures ready
- Test disaster recovery procedures

This troubleshooting guide should help resolve most common issues. For persistent problems, consider reviewing the service-specific logs and consulting the API documentation for detailed error codes and responses.
