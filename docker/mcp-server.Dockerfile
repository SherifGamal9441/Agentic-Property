FROM python:3.11-slim

WORKDIR /app
COPY docker/mcp-server-requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8001
ENV MCP_TRANSPORT=streamable-http
EXPOSE 8001

CMD ["python", "-m", "src.mcp.server"]