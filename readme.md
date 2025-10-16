for chatpro

## OpenWebUI: Use local git clone for easy code edits

This project runs [OpenWebUI] from a local git clone so you can modify its code directly and rebuild quickly.

### Prerequisites
- Docker (with either `docker compose` plugin or `docker-compose`)
- Git

### Setup
1. Copy the env file and adjust if needed:
   ```bash
   cp .env.example .env
   ```
2. Clone OpenWebUI locally (default repo/branch can be overridden in `.env`):
   ```bash
   make clone
   ```

### Run
Build and start OpenWebUI from the local clone:
```bash
make up
```
The UI will be available at http://localhost:8080 unless you changed `OPENWEBUI_PORT`.

### Developing
- Edit code inside the `open-webui` directory.
- Rebuild after changes:
  ```bash
  make build && make restart
  ```

### Useful commands
```bash
make logs     # Tail service logs
make down     # Stop containers
make clean    # Remove containers and data
```

[OpenWebUI]: https://github.com/open-webui/open-webui
