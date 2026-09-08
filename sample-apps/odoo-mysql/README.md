# Odoo MySQL Sample App

A containerized Odoo application demonstrating Aikido security protection with MySQL database integration.

## Overview

This sample app uses:
- **Odoo 16.0** - Popular open-source ERP/web framework
- **PostgreSQL** - Required by Odoo core
- **MySQL** - Used by the custom dog management module
- **Docker** - Containerized deployment following official Odoo on-premise guidelines

## Architecture

The app consists of:
- Custom Odoo addon module (`dog_management`) with HTTP controllers
- Vulnerable endpoints for testing security features (SQL injection, command injection, path traversal, SSRF)
- Aikido firewall integration via Python middleware

## Getting Started

### Prerequisites
- Docker and Docker Compose installed
- Ports 8114 and 8115 available

### Build and Run

```bash
# Build the Docker image
make build

# Run with Aikido protection (port 8114)
make run

# Run without Aikido protection (port 8115)
make runZenDisabled

# Run in background
make up

# View logs
make logs

# Stop services
make down
```

## Accessing the Application

- **With Aikido**: http://localhost:8114
- **Without Aikido**: http://localhost:8115 (use `make runZenDisabled`)

On first access, you'll need to create an Odoo database:
1. Set master password: `admin`
2. Database name: `odoo_demo`
3. Email: any email
4. Password: any password
5. Demo data: optional

The `dog_management` module will be automatically installed.

## Testing Vulnerabilities

### SQL Injection
- Create a dog with name: `Malicious dog", 1); -- `
- Visit: http://localhost:8114/create/via_query?dog_name=test%22%20OR%201=1--

### Command Injection
- Visit: http://localhost:8114/shell
- Enter command: `ls -la`

### Path Traversal
- Visit: http://localhost:8114/open_file
- Enter filepath: `/etc/passwd`

### SSRF
- Visit: http://localhost:8114/request
- Enter URL: `http://localhost:5000`

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Homepage - lists all dogs |
| `/dogpage/<id>` | GET | View specific dog details |
| `/create` | GET/POST | Create new dog form/handler |
| `/create/via_query?dog_name=X` | GET | Create dog via query parameter |
| `/multiple_queries` | POST | Execute 20 queries (performance test) |
| `/shell` | GET/POST | Execute shell commands |
| `/open_file` | GET/POST | Read files from filesystem |
| `/request` | GET/POST | Make HTTP requests (SSRF test) |
| `/test_ratelimiting_1` | GET | Rate limiting test endpoint |

## Development

### Project Structure
```
odoo-mysql/
├── addons/
│   └── dog_management/          # Custom Odoo module
│       ├── __init__.py
│       ├── __manifest__.py      # Module metadata
│       └── controllers/
│           ├── __init__.py
│           └── main.py          # HTTP controllers
├── docker-compose.yml           # Multi-container setup
├── Dockerfile                   # Custom Odoo image
├── odoo.conf                    # Odoo configuration
├── Makefile                     # Build/run commands
└── README.md
```

### Useful Commands

```bash
# Access Odoo container shell
make shell

# Clean up everything (including volumes)
make clean

# Restart services
make restart

# Check application health
make health-check
```

## Notes

- Odoo requires PostgreSQL for its core functionality
- The dog management module uses MySQL to demonstrate multi-database scenarios
- Aikido protection is configured via environment variables
- The app auto-installs the `dog_management` module on first run
- Port 8114 runs **with** Aikido protection
- Port 8115 runs **without** Aikido protection (for comparison)
