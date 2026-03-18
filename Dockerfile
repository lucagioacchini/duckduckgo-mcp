FROM python:3.11-alpine

RUN apk add --no-cache gcc musl-dev linux-headers

WORKDIR /app

COPY pyproject.toml .
COPY src ./src

RUN pip install --upgrade pip
RUN pip install -e .

COPY . .

# Run the MCP server
CMD ["python", "server.py"]
