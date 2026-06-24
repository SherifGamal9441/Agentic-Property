# Setup & Run

## 1. Create .env file (parent directory, same level as dld-mcp-server)

Create `..\.env` with:

```
RAPIDAPI_KEY=your_key_here
EXCHANGERATE_API_KEY=your_key_here
```

## 2. Build and start all services

```powershell
docker compose --env-file .env -f dld-mcp-server\docker-compose.yml up --build -d
```

Wait ~30s for data-service to seed 28K historical records.

## 3. Scrape active listings (optional but recommended)

```powershell
docker exec dld-mcp-server-data-service-1 python scraper.py 90
```

## 4. Test with MCP Inspector

```powershell
npx @modelcontextprotocol/inspector
```

Open browser at `http://localhost:6274`, enter SSE URL:

```
http://localhost:8001/sse
```

## 5. Test search API directly

```powershell
curl.exe -X POST http://localhost:8000/search/historical -H "Content-Type: application/json" -d "{}"

curl.exe -X POST http://localhost:8000/search/active -H "Content-Type: application/json" -d "{}"
```
