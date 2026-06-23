cd dld-mcp-server
docker-compose --env-file ..\.env up --build
docker exec -it dld-mcp-server-data-service-1 python scraper.py 5 
