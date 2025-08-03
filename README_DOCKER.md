# Haystack Docker Setup

This directory contains the Docker containerization setup for the Haystack Web Collector Suite, breaking it into three main services:

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │    Database     │
│   (Nginx)       │────│   (FastAPI)     │────│   (MariaDB)     │
│   Port: 80      │    │   Port: 8000    │    │   Port: 3306    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                       ┌─────────────────┐
                       │ Scraper Workers │
                       │  (Background)   │
                       └─────────────────┘
```

## Services

### 1. Database (MariaDB)
- **Container**: `haystack_db`
- **Port**: 3306
- **Purpose**: Stores all scraped data, configurations, and system status
- **Features**:
  - Automatic schema creation
  - Initial data seeding
  - Health checks
  - Persistent volume storage

### 2. Backend API (FastAPI)
- **Container**: `haystack_backend`
- **Port**: 8000
- **Purpose**: REST API for managing scraping engines and data
- **Features**:
  - RESTful API endpoints
  - Background job processing
  - Engine management
  - Health monitoring
  - Automatic API documentation at `/docs`

### 3. Frontend UI (Nginx + HTML/JS)
- **Container**: `haystack_ui`
- **Port**: 80
- **Purpose**: Web interface for monitoring and controlling the system
- **Features**:
  - Dashboard with system metrics
  - Engine management interface
  - Data browsing and search
  - System configuration
  - Real-time status updates

### 4. Scraper Workers (Optional)
- **Containers**: `scraper-worker` (scalable)
- **Purpose**: Dedicated containers for running scraping tasks
- **Features**:
  - Horizontal scaling
  - Independent processing
  - Configurable worker types

## Quick Start

1. **Copy environment file:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` file with your preferred settings (database passwords, etc.)

2. **Start all services:**
   ```bash
   docker-compose up -d
   ```

3. **Check service health:**
   ```bash
   docker-compose ps
   ```

4. **Access the web interface:**
   Open http://localhost in your browser

5. **Access the API documentation:**
   Open http://localhost:8000/docs in your browser

## Detailed Setup

### Environment Configuration

The `.env` file contains important configuration options:

```bash
# Database settings
DB_ROOT_PASSWORD=your-secure-root-password
DB_PASSWORD=your-secure-user-password

# API settings
API_SECRET_KEY=your-secret-key-for-jwt

# Scraping settings
MAX_CONCURRENT_SCRAPERS=5
DEFAULT_DELAY_MIN=1
DEFAULT_DELAY_MAX=10
```

### Data Persistence

The following directories are mapped for data persistence:
- `./data/downloads` → Downloaded files
- `./data/haystack` → Haystack file processing
- `./logs` → Application logs
- Database data is stored in a Docker volume

### Service Management

**Start services:**
```bash
docker-compose up -d
```

**View logs:**
```bash
docker-compose logs -f [service-name]
```

**Stop services:**
```bash
docker-compose down
```

**Rebuild services:**
```bash
docker-compose build [service-name]
docker-compose up -d [service-name]
```

**Scale workers:**
```bash
docker-compose up -d --scale scraper-worker=3
```

## API Endpoints

The backend API provides the following main endpoints:

### System
- `GET /health` - System health check
- `GET /api/config` - Get system configuration
- `PUT /api/config/{key}` - Update configuration

### Engines
- `GET /api/engines` - List all engines
- `POST /api/engines/{name}/start` - Start an engine
- `POST /api/engines/{name}/stop` - Stop an engine

### Items
- `GET /api/items` - List collected items (paginated)
- `GET /api/items/{id}` - Get specific item details

### Status
- `GET /api/status` - Get system status messages

### Jobs
- `POST /api/jobs/scrape` - Create new scraping job

## Web Interface Features

### Dashboard
- System health overview
- Active engines count
- Total items collected
- Recent activity log
- Quick action buttons

### Engine Management
- Start/stop engines
- View engine status
- Monitor engine activity

### Data Browser
- Browse collected items
- Search functionality
- View item details
- Pagination support

### Configuration
- Update system settings
- Manage scraping parameters
- View current configuration

## Development

### Adding New Engines

1. Create your engine class in the `engines/` directory
2. Ensure it inherits from `PeregrinBase`
3. The engine will be automatically available via the API

### Custom Configuration

You can override the default Docker Compose configuration by creating a `docker-compose.override.yml` file.

### Database Access

Connect to the database directly:
```bash
docker-compose exec database mysql -u peregrin -p Peregrin
```

### Debugging

View backend logs:
```bash
docker-compose logs -f backend
```

Access backend container:
```bash
docker-compose exec backend bash
```

## Security Considerations

### Production Deployment

1. **Change default passwords** in `.env` file
2. **Use strong API secret keys**
3. **Configure firewall rules** to restrict database access
4. **Enable HTTPS** by adding SSL certificates to Nginx
5. **Limit resource usage** with Docker resource constraints
6. **Regular backups** of the database volume

### Network Security

The services communicate through a private Docker network. Only the frontend (port 80) is exposed by default.

## Monitoring

### Health Checks

All services include health checks:
- Database: MariaDB connection test
- Backend: API endpoint response
- Frontend: Nginx status page

### Logs

Centralized logging is available through Docker Compose:
```bash
docker-compose logs -f --tail=100
```

### Metrics

The backend API provides system metrics that can be integrated with monitoring tools like Prometheus or Grafana.

## Troubleshooting

### Common Issues

1. **Database connection failed**
   - Check if database container is running
   - Verify credentials in `.env` file
   - Wait for database initialization to complete

2. **Backend API not responding**
   - Check backend container logs
   - Verify database connectivity
   - Ensure all dependencies are installed

3. **Frontend not loading**
   - Check if backend is accessible
   - Verify Nginx configuration
   - Check browser console for errors

4. **Permission errors**
   - Ensure Docker has necessary permissions
   - Check file ownership in mounted volumes

### Getting Help

1. Check container logs: `docker-compose logs [service]`
2. Verify service health: `docker-compose ps`
3. Test API endpoints: `curl http://localhost:8000/health`
4. Check database connectivity: `docker-compose exec database mysql -u peregrin -p`

## Maintenance

### Database Backup

```bash
docker-compose exec database mysqldump -u root -p Peregrin > backup.sql
```

### Database Restore

```bash
docker-compose exec -T database mysql -u root -p Peregrin < backup.sql
```

### Update Services

```bash
docker-compose pull
docker-compose up -d
```

This will pull the latest images and recreate containers as needed.