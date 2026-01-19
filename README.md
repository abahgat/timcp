# Travel Impact Model MCP Server

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-1.0-green.svg)](https://modelcontextprotocol.io)

A Model Context Protocol (MCP) server that wraps the Google Travel Impact Model API, providing tools to calculate flight emissions for typical flights, specific flights, and Scope 3 reporting.

## What is this?

This MCP server allows AI assistants (Claude, Gemini, etc.) to calculate flight emissions using Google's Travel Impact Model API. Instead of manually calling the API, your AI assistant can automatically look up emissions data when helping with travel planning or sustainability reporting.

**Use cases:**
- Compare flight options by environmental impact
- Calculate emissions for corporate travel reporting
- Generate Scope 3 GHG emissions reports
- Make data-driven decisions about sustainable travel

## Features

- **6 tools** for calculating flight emissions
- **Batch processing** support for efficient multi-flight queries
- **Scope 3 reporting** compatible (WTW, TTW, WTT emissions)
- **Streamable HTTP transport** for multi-client support

## Demo

[![Demo: Using Claude Code to calculate flight emissions with the Travel Impact Model MCP server](https://asciinema.org/a/769163.svg)](https://asciinema.org/a/769163)

Watch how to use this MCP server with Claude Code to:
- Calculate typical flight emissions between airports
- Compare specific flights for environmental impact
- Generate Scope 3 emissions reports from CSV data

## Installation

### Prerequisites

- Python 3.12 or higher
- [Google Travel Impact Model API key](https://developers.google.com/travel/impact-model/docs/getting-started)
- Docker (optional, for containerized deployment)

### Option 1: Docker (Recommended)

1. Clone the repository:

```bash
git clone https://github.com/yourusername/timcp.git
cd timcp
```

2. Create a `.env` file with your API key:

```bash
echo "TRAVEL_IMPACT_MODEL_API_KEY=your_api_key_here" > .env
```

> **Note**: The `.env` file is in `.gitignore` to prevent committing secrets.

3. Start the server:

```bash
docker-compose up
```

The server is now running at `http://localhost:8080/mcp`.

### Option 2: Local Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/timcp.git
cd timcp
```

2. Install with uv (recommended):

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

Or with pip:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

3. Create a `.env` file with your API key:

```bash
echo "TRAVEL_IMPACT_MODEL_API_KEY=your_api_key_here" > .env
```

Then load it:

```bash
set -a; source .env; set +a
```

> **Note**: The `.env` file is in `.gitignore` to prevent committing secrets.

4. Run the server:

```bash
uvicorn mcp_tim_wrapper.main:app --host 127.0.0.1 --port 8080
```

The server is now running at `http://localhost:8080/mcp`.

## Quick Start

## Configuring MCP Clients

Once the server is running (locally or via Docker), configure your MCP client to connect.

### Claude Desktop

Add to your config file:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "tim": {
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

### Claude Code

```bash
claude mcp add --transport http tim http://localhost:8080/mcp
```

### Gemini CLI

```bash
gemini mcp add --transport http --scope project tim http://localhost:8080/mcp
```

Use `--scope user` for global configuration instead of project-specific.

### Other MCP Clients

Point your client to the MCP endpoint: `http://localhost:8080/mcp`

## Available Tools

| Tool | Description | Use When |
|------|-------------|----------|
| `tim_get_typical_flight_emissions` | Average emissions between two airports based on historical data | You want general estimates without specific flight details |
| `tim_get_specific_flight_emissions` | Emissions for a specific flight number on a future date | You're comparing actual flight options for booking |
| `tim_get_scope3_flight_emissions` | GHG emissions for Scope 3 reporting (past flights only) | You need WTW/TTW/WTT breakdowns for sustainability reports |
| `tim_get_typical_flight_emissions_batch` | Batch version for multiple airport pairs | Processing many routes at once |
| `tim_get_specific_flight_emissions_batch` | Batch version for multiple future flights | Comparing many flight options efficiently |
| `tim_get_scope3_flight_emissions_batch` | Batch version for multiple past flights | Generating quarterly/annual emissions reports |

## Usage Examples

### Get Typical Flight Emissions

Request emissions estimate for flights between two airports:

```json
{
  "tool": "tim_get_typical_flight_emissions",
  "arguments": {
    "origin": "BOS",
    "destination": "LAX"
  }
}
```

Response:

```json
{
  "typicalFlightEmissions": [
    {
      "market": {
        "origin": "BOS",
        "destination": "LAX"
      },
      "emissionsGramsPerPax": {
        "economy": 150000,
        "premiumEconomy": 225000,
        "business": 435000,
        "first": 600000
      }
    }
  ],
  "modelVersion": {
    "major": 1,
    "minor": 9,
    "patch": 0
  }
}
```

### Get Specific Flight Emissions

Request emissions for a specific flight (must be a future date):

```json
{
  "tool": "tim_get_specific_flight_emissions",
  "arguments": {
    "origin": "SFO",
    "destination": "LHR",
    "operating_carrier_code": "UA",
    "flight_number": 901,
    "departure_year": 2026,
    "departure_month": 3,
    "departure_day": 15
  }
}
```

Response:

```json
{
  "flightEmissions": [
    {
      "flight": {
        "origin": "SFO",
        "destination": "LHR",
        "operatingCarrierCode": "UA",
        "flightNumber": 901,
        "departureDate": {
          "year": 2026,
          "month": 3,
          "day": 15
        }
      },
      "emissionsGramsPerPax": {
        "economy": 500000,
        "premiumEconomy": 750000,
        "business": 1450000,
        "first": 2000000
      }
    }
  ],
  "modelVersion": {
    "major": 1,
    "minor": 9,
    "patch": 0
  }
}
```

### Get Scope 3 Flight Emissions

Request emissions for past travel (Scope 3 reporting). You must provide either origin/destination OR distance_km:

**Using origin/destination:**

```json
{
  "tool": "tim_get_scope3_flight_emissions",
  "arguments": {
    "departure_year": 2024,
    "departure_month": 10,
    "departure_day": 15,
    "cabin_class": "ECONOMY",
    "origin": "JFK",
    "destination": "SFO"
  }
}
```

**Using distance:**

```json
{
  "tool": "tim_get_scope3_flight_emissions",
  "arguments": {
    "departure_year": 2024,
    "departure_month": 10,
    "departure_day": 15,
    "cabin_class": "BUSINESS",
    "distance_km": "5000"
  }
}
```

Response:

```json
{
  "flightEmissions": [
    {
      "flight": {
        "departureDate": {
          "year": 2024,
          "month": 10,
          "day": 15
        },
        "cabinClass": "ECONOMY",
        "origin": "JFK",
        "destination": "SFO"
      },
      "wtwEmissionsGramsPerPax": "123456",
      "ttwEmissionsGramsPerPax": "100000",
      "wttEmissionsGramsPerPax": "23456",
      "source": "TIM_EMISSIONS"
    }
  ],
  "modelVersion": {
    "major": 2,
    "minor": 0,
    "patch": 0
  }
}
```

### Batch Processing

For multiple queries, use batch endpoints for efficiency:

**Request:**

```json
{
  "tool": "tim_get_typical_flight_emissions_batch",
  "arguments": {
    "markets": [
      {"origin": "JFK", "destination": "LAX"},
      {"origin": "SFO", "destination": "LHR"},
      {"origin": "ORD", "destination": "CDG"}
    ]
  }
}
```

**Response:**

```json
{
  "typicalFlightEmissions": [
    {
      "market": {
        "origin": "JFK",
        "destination": "LAX"
      },
      "emissionsGramsPerPax": {
        "economy": 180000,
        "premiumEconomy": 270000,
        "business": 522000,
        "first": 720000
      }
    },
    {
      "market": {
        "origin": "SFO",
        "destination": "LHR"
      },
      "emissionsGramsPerPax": {
        "economy": 550000,
        "premiumEconomy": 825000,
        "business": 1595000,
        "first": 2200000
      }
    },
    {
      "market": {
        "origin": "ORD",
        "destination": "CDG"
      },
      "emissionsGramsPerPax": {
        "economy": 480000,
        "premiumEconomy": 720000,
        "business": 1392000,
        "first": 1920000
      }
    }
  ],
  "modelVersion": {
    "major": 1,
    "minor": 9,
    "patch": 0
  }
}
```

**Scope 3 Batch Example:**

Process multiple past flights for sustainability reporting:

```json
{
  "tool": "tim_get_scope3_flight_emissions_batch",
  "arguments": {
    "flights": [
      {
        "departureDate": {"year": 2024, "month": 1, "day": 15},
        "origin": "BOS",
        "destination": "SFO",
        "carrierCode": "B6",
        "flightNumber": 333,
        "cabinClass": "ECONOMY"
      },
      {
        "departureDate": {"year": 2024, "month": 2, "day": 3},
        "origin": "BOS",
        "destination": "LAX",
        "carrierCode": "DL",
        "flightNumber": 318,
        "cabinClass": "BUSINESS"
      }
    ]
  }
}
```

This returns WTW (well-to-wake), TTW (tank-to-wake), and WTT (well-to-tank) emissions for each flight, essential for accurate Scope 3 GHG reporting.

## Error Handling

The server returns `ToolError` for various error conditions:

### Invalid Airport Code

```json
{
  "error": "TIM API Error (400): Invalid IATA code: XXX"
}
```

### Flight Not Found

```json
{
  "error": "TIM API Error (404): Flight UA999 not found for the specified date"
}
```

### Invalid Cabin Class

Valid cabin classes for Scope 3: `ECONOMY`, `PREMIUM_ECONOMY`, `BUSINESS`, `FIRST`

```json
{
  "error": "TIM API Error (400): Invalid cabin class: INVALID"
}
```

### Missing API Key

If `TRAVEL_IMPACT_MODEL_API_KEY` is not set, the server will fail to start:

```
ValueError: TRAVEL_IMPACT_MODEL_API_KEY environment variable not set.
```

### Rate Limiting

The Google Travel Impact Model API may rate limit requests. Handle accordingly:

```json
{
  "error": "TIM API Error (429): Rate limit exceeded"
}
```

## Security Considerations

### API Key Storage

- **Never commit API keys** to version control
- Store the API key in environment variables
- For production, use a secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.)
- The API key is passed as a URL query parameter to Google's API (Google's required pattern)

### Network Security

- By default, the server binds to `0.0.0.0` - restrict this in production
- Use HTTPS in production (configure via reverse proxy like nginx)
- CORS is configured to allow localhost origins by default
- Set `ALLOWED_ORIGINS` environment variable for production:
  ```bash
  export ALLOWED_ORIGINS="https://yourdomain.com"
  ```

### Access Control

- This server does not implement authentication
- Deploy behind an API gateway or reverse proxy for access control
- Consider rate limiting at the infrastructure level

## Testing

Install test dependencies and run tests:

```bash
uv pip install -e .[test]
pytest
```

Run with verbose output:

```bash
pytest -v
```

## Development

### Releasing

To create a new release:
1. Ensure you are on the `main` branch and have no uncommitted changes.
2. Run the release helper script:
   ```bash
   ./scripts/release.sh
   ```
3. Follow the prompts to enter the new version number.

The script will:
- Update the version in `pyproject.toml`
- Create a git commit and tag
- Push to GitHub
- Trigger the CI/CD pipeline which builds the Docker image and publishes it to GitHub Container Registry (GHCR) and creates a GitHub Release.

### Running Without Docker

```bash
uv venv
source .venv/bin/activate
uv pip install -e .

# Set API key (see Installation section for .env file method)
export TRAVEL_IMPACT_MODEL_API_KEY="your_api_key_here"

# Run the server
uvicorn mcp_tim_wrapper.main:app --host 127.0.0.1 --port 8080
```

### Linting and Formatting

```bash
uv pip install -e .[dev]
ruff check .
black .
```

## Contributing

Contributions are welcome! Here's how you can help:

1. **Report bugs** - Open an issue describing the problem
2. **Suggest features** - Share ideas for improvements
3. **Submit PRs** - Fix bugs or add features

### Development Setup

```bash
# Clone and install
git clone https://github.com/yourusername/timcp.git
cd timcp
uv venv
source .venv/bin/activate
uv pip install -e .[dev,test]

# Run tests
pytest

# Run linting
ruff check .
black --check .

# Format code
black .
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mcp_tim_wrapper

# Run specific test file
pytest tests/test_tools.py -v
```

## License

Apache License 2.0

## Acknowledgments

- Built with the [Model Context Protocol SDK](https://github.com/anthropics/mcp)
- Uses [Google's Travel Impact Model API](https://developers.google.com/travel/impact-model)
- Powered by [FastAPI](https://fastapi.tiangolo.com/) and [httpx](https://www.python-httpx.org/)
