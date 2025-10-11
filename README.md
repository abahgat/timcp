# MCP Travel Impact Model Wrapper

A Model Context Protocol (MCP) server that acts as a wrapper for the Google Travel Impact Model API. This server provides tools to calculate flight emissions for typical flights, specific flights, and for Scope 3 reporting.

## Setup

1.  **Install Dependencies:**
    This project uses `uv` for dependency management. To install the required packages, first create a virtual environment, then install the dependencies in editable mode.
    ```bash
    uv venv
    source .venv/bin/activate
    uv pip install -e .
    ```

2.  **Set API Key:**
    You will need a Google Travel Impact Model API key. Set it as an environment variable:
    ```bash
    export TRAVEL_IMPACT_API_KEY="your_api_key_here"
    ```

## Running the Server

To run the MCP server, use the following command:
```bash
uvicorn src.mcp_tim_wrapper.main:app --host 0.0.0.0 --port 8080
```
