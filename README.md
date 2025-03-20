# GameApp Application

A FastAPI application with Telegram bot integration.

## Docker Setup

This application is containerized using Docker and can be run using Docker Compose.

### Prerequisites

- Docker
- Docker Compose

### Configuration

All configuration is done through environment variables. You can modify the `.env` file to change the configuration.

### Running the Application

1. Build and start the containers:

```bash
docker-compose up -d
```

2. View logs:

```bash
docker-compose logs -f
```

3. Stop the application:

```bash
docker-compose down
```

### Environment Variables

- `TELEGRAM_BOT_WEBHOOK_SECRET`: Secret token for Telegram webhook authentication
- `TELEGRAM_BOT_WEBHOOK_HOST`: Host URL for Telegram webhook
- `TELEGRAM_BOT_TOKEN`: Telegram Bot API token
- `FRONTEND_URL`: URL of the frontend application
- `AUTH_CHECK_TELEGRAM_TOKEN`: Whether to check Telegram token for authentication
- `DB_PATH`: Path to the SQLite database file

## Development

### Project Structure

- `app/`: Main application code
  - `game/`: Game-related functionality
- `config.py`: Configuration file
- `cron/`: Cron jobs
- `Dockerfile`: Docker configuration
- `docker-compose.yaml`: Docker Compose configuration

### Database

The application uses SQLite for data storage. The database file is stored in a Docker volume to persist data between container restarts.
