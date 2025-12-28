# Production Deployment

## Pre-Deployment Checklist

### Security

- [ ] **Change all default passwords and secrets** in your `.env` file
  - `DATABASE_PASSWORD`: Use a strong, randomly generated password
  - `JWT_SECRET_KEY`: Use a high-entropy secret (see [Configuration](../configuration.md))
- [ ] **Set proper CORS origins** - Never use `["*"]` in production
  - Use explicit origins: `["https://yourdomain.com", "https://app.yourdomain.com"]`
- [ ] **Use environment variables** instead of `.env` file for secrets
  - Use your platform's secret management (AWS Secrets Manager, HashiCorp Vault, etc.)
- [ ] **Enable HTTPS** via reverse proxy (see below)
- [ ] **Review RLS policies** to ensure they match your security requirements

### Infrastructure

- [ ] **Set up database backups**
  - Configure automated PostgreSQL backups
  - Test restore procedures
  - Set retention policy (e.g., 30 days)
- [ ] **Configure logging and monitoring**
  - Set up log aggregation (ELK, Datadog, etc.)
  - Configure health check monitoring
  - Set up alerts for errors and high latency
- [ ] **Set resource limits**
  - Configure Docker/container resource limits
  - Set database connection pool sizes appropriately
- [ ] **Use a reverse proxy** for HTTPS termination
  - Nginx, Traefik, or cloud load balancer
  - Configure SSL/TLS certificates (Let's Encrypt recommended)

### Configuration

- [ ] **Set `ENVIRONMENT=production`**
- [ ] **Set `DEBUG=false`**
- [ ] **Configure `DATABASE_SERVICE_URL`** if using public submissions
  - Use a separate database user with limited permissions
  - Document which operations use the service role
- [ ] **Review rate limiting** settings
  - Adjust limits based on expected traffic
  - Configure per-IP and per-user limits appropriately

## Reverse Proxy Configuration

### Nginx Example

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Traefik Example

```yaml
services:
  formcore-backend:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.formcore.rule=Host(`api.yourdomain.com`)"
      - "traefik.http.routers.formcore.entrypoints=websecure"
      - "traefik.http.routers.formcore.tls.certresolver=letsencrypt"
```

## Database Backups

### Manual Backup

```bash
docker compose exec formcore-db pg_dump -U postgres formcore > backup.sql
```

### Automated Backups

Set up a cron job or scheduled task:

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
docker compose exec -T formcore-db pg_dump -U postgres formcore > "$BACKUP_DIR/formcore_$DATE.sql"
# Keep only last 30 days
find "$BACKUP_DIR" -name "formcore_*.sql" -mtime +30 -delete
```

### Restore

```bash
cat backup.sql | docker compose exec -T formcore-db psql -U postgres formcore
```

## Monitoring

### Health Checks

Monitor the `/health` endpoint:

- Expected response: `200 OK` with system information
- Set up alerts if health check fails

### Key Metrics to Monitor

- Request rate and latency
- Database connection pool usage
- Error rates (4xx, 5xx responses)
- JWT token validation failures
- RLS policy violations (check logs)

### Logging

Ensure structured logging is configured. FormCore logs include:

- Request/response details with user context
- Authentication events
- Database errors
- Application errors

## Scaling Considerations

- **Horizontal scaling**: Multiple backend instances can share the same database
- **Database connection pooling**: Adjust `pool_size` and `max_overflow` in `app/core/db/session.py`
- **Load balancing**: Use a load balancer that supports sticky sessions (if needed) or stateless design
- **Database read replicas**: Consider read replicas for read-heavy workloads (future enhancement)

## Disaster Recovery

1. **Regular backups** (see above)
2. **Test restore procedures** quarterly
3. **Document recovery runbook**
4. **Keep secrets backed up securely** (encrypted, separate from database backups)
