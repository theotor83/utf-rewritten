# Redis Security Configuration

This directory contains the secure Redis configuration for the UTF-Rewritten Forum.

## Security Features Implemented

### 1. **Authentication Required**
- Redis requires a password for all connections
- Password is set via the `REDIS_PASSWORD` environment variable
- No anonymous access allowed

### 2. **Network Security**
- Redis port (6379) is **NOT exposed** to the host machine
- Only Docker services can communicate with Redis internally
- Protected mode is enabled

### 3. **Command Security**
- Dangerous Redis commands are disabled:
  - `FLUSHDB` - Prevents accidental database deletion
  - `FLUSHALL` - Prevents accidental deletion of all databases
  - `KEYS` - Prevents performance issues in production
  - `CONFIG` - Prevents configuration changes
  - `SHUTDOWN` - Prevents unauthorized shutdown
  - `DEBUG` - Prevents debug access
  - `EVAL` - Prevents arbitrary Lua script execution

### 4. **Resource Limits**
- Maximum memory: 512MB with LRU eviction policy
- Maximum clients: 100 concurrent connections
- Client timeout: 5 minutes for idle connections

### 5. **Data Persistence**
- AOF (Append Only File) enabled for data durability
- Automatic saves configured for data protection

## Setup Instructions

### 1. **Set Redis Password**
Create a `.env` file in your project root (copy from `env.example`):

```bash
# Generate a strong password (minimum 32 characters)
REDIS_PASSWORD=your-very-secure-redis-password-at-least-32-chars-long
```

**Important**: Use a cryptographically secure random password generator.

### 2. **Start the Services**
```bash
docker-compose up -d redis
```

### 3. **Verify Security**
Check that Redis is not accessible from outside Docker:
```bash
# This should fail (connection refused)
redis-cli -h localhost -p 6379 ping

# This should also fail (no external port)
telnet localhost 6379
```

### 4. **Test Internal Connectivity**
From within the web container:
```bash
docker-compose exec web python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'success')
>>> cache.get('test')
'success'
```

## Configuration Files

- **`redis.conf`**: Main Redis configuration with security settings
- **`entrypoint.sh`**: Docker entrypoint script that processes environment variables
- **`README.md`**: This documentation file

## Security Best Practices

### 1. **Password Management**
- Use unique, strong passwords (32+ characters)
- Store passwords securely (environment variables, not in code)
- Rotate passwords regularly in production
- Never commit passwords to version control

### 2. **Network Security**
- Keep Redis internal to Docker network only
- Use firewall rules if exposing Redis externally (not recommended)
- Monitor Redis logs for suspicious activity

### 3. **Monitoring**
- Monitor Redis memory usage
- Watch for failed authentication attempts
- Set up alerts for unusual connection patterns

### 4. **Backup and Recovery**
- Regular backups of Redis data (`/data` volume)
- Test restoration procedures
- Consider Redis replication for high availability

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```
   Error: NOAUTH Authentication required
   ```
   - Check that `REDIS_PASSWORD` is set in `.env`
   - Verify Django `REDIS_URL` includes password

2. **Connection Refused**
   ```
   Error: Connection refused
   ```
   - Normal if trying to connect from outside Docker
   - Check Docker network connectivity for internal services

3. **Configuration Errors**
   ```
   Error: Bad directive or wrong number of arguments
   ```
   - Check `redis.conf` syntax
   - Verify environment variable substitution in entrypoint script

### Debug Commands

```bash
# Check Redis container logs
docker-compose logs redis

# Test Redis configuration
docker-compose exec redis redis-server /usr/local/etc/redis/redis.conf --test-memory-config

# Connect to Redis from web container
docker-compose exec web redis-cli -h redis -a $REDIS_PASSWORD ping
```

## Migration from Unsecured Redis

If migrating from an unsecured Redis setup:

1. **Export existing data** (if needed):
   ```bash
   docker-compose exec redis redis-cli --rdb /data/backup.rdb
   ```

2. **Update configuration** as described above

3. **Restart services**:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

4. **Import data** (if needed):
   ```bash
   docker-compose exec redis redis-cli -a $REDIS_PASSWORD --rdb /data/backup.rdb
   ```

## Production Considerations

- Use Redis Sentinel or Cluster for high availability
- Implement proper monitoring and alerting
- Regular security audits and password rotation
- Consider Redis encryption in transit (TLS)
- Backup and disaster recovery procedures 