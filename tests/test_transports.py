import os
import sys
import subprocess
import socket
import pytest
import httpx
import anyio
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client

# Load environment variables
load_dotenv()

# Skip all tests in this module if API key is missing
if "TRAVEL_IMPACT_MODEL_API_KEY" not in os.environ:
    pytest.skip(
        "TRAVEL_IMPACT_MODEL_API_KEY not found in environment. Skipping transport tests.",
        allow_module_level=True,
    )

pytestmark = pytest.mark.anyio


def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture
async def http_server_url():
    """
    Fixture that starts the MCP server on a random port and returns the base URL.
    """
    port = get_free_port()
    env = os.environ.copy()

    # Start the server process
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "mcp_tim_wrapper.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    base_url = f"http://127.0.0.1:{port}"
    server_started = False

    try:
        # Wait for server to start (up to 10 seconds)
        for _ in range(20):
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(f"{base_url}/health")
                    if resp.status_code == 200:
                        server_started = True
                        break
            except httpx.ConnectError:
                pass
            await anyio.sleep(0.5)

        if not server_started:
            stdout, stderr = process.communicate()
            raise RuntimeError(
                f"Server failed to start.\nStdout: {stdout.decode()}\nStderr: {stderr.decode()}"
            )

        yield base_url

    finally:
        # Cleanup
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()


async def test_stdio_transport():
    """
    Tests that the server works over Stdio transport.
    """
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_tim_wrapper.main"],
        env=os.environ.copy(),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List tools
            tools = await session.list_tools()
            assert len(tools.tools) > 0, "No tools found via Stdio"

            # Call a tool
            try:
                await session.call_tool(
                    "tim_get_typical_flight_emissions",
                    arguments={"origin": "JFK", "destination": "LHR"},
                )
            except Exception as e:
                # If it's an API error, the transport is working.
                error_str = str(e)
                if any(
                    msg in error_str for msg in ["TIM API Error", "400", "403", "401"]
                ):
                    pass
                else:
                    raise


async def test_streamable_http_transport(http_server_url):
    """
    Tests that the server works over Streamable HTTP transport (FastMCP default).
    """
    async with streamable_http_client(f"{http_server_url}/mcp") as (read, write, *_):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List tools
            tools = await session.list_tools()
            assert len(tools.tools) > 0, "No tools found via HTTP"

            # Call a tool
            try:
                await session.call_tool(
                    "tim_get_typical_flight_emissions",
                    arguments={"origin": "SFO", "destination": "NRT"},
                )
            except Exception as e:
                # If it's an API error, the transport is working.
                error_str = str(e)
                if any(
                    msg in error_str for msg in ["TIM API Error", "400", "403", "401"]
                ):
                    pass
                else:
                    raise
