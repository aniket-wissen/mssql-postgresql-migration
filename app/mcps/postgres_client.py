import requests
import json

MCP_SERVER_URL = "http://localhost:8000/mcp"
HEADERS_BASE = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream"
}


class MCPPostgresClient:
    """
    MCP client that talks to FastMCP PostgreSQL server.
    Handles session initialization and tool calls properly.
    """

    def __init__(self):
        self.session_id = None
        self._initialize_session()

    def _initialize_session(self):
        """Initialize MCP session and get session ID."""
        try:
            response = requests.post(
                MCP_SERVER_URL,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "migration-client", "version": "1.0"}
                    }
                },
                headers=HEADERS_BASE,
                stream=True,
                timeout=30
            )
            self.session_id = response.headers.get("mcp-session-id")
            print(f"    [MCP Client] Session initialized: {self.session_id}")
        except Exception as e:
            raise Exception(f"MCP Server not running! Start it with: python app/mcp_server.py. Error: {e}")

    def _call(self, tool_name: str, arguments: dict) -> str:
        """Call a tool on the MCP server using session ID."""
        try:
            headers = {**HEADERS_BASE, "mcp-session-id": self.session_id}
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            response = requests.post(
                MCP_SERVER_URL,
                json=payload,
                headers=headers,
                stream=True,
                timeout=30
            )
            # Parse SSE response
            for line in response.iter_lines():
                if line:
                    decoded = line.decode("utf-8")
                    if decoded.startswith("data:"):
                        data = json.loads(decoded[5:].strip())
                        if "result" in data:
                            content = data["result"].get("content", [])
                            if content:
                                return content[0].get("text", "")
            return "ERROR: No response"
        except Exception as e:
            raise Exception(f"MCP call failed: {e}")

    def execute_sql(self, sql: str) -> str:
        print(f"    [MCP Client] execute_sql: {sql[:60]}...")
        return self._call("execute_sql", {"sql": sql})

    def query_sql(self, sql: str) -> str:
        print(f"    [MCP Client] query_sql: {sql[:60]}...")
        return self._call("query_sql", {"sql": sql})

    def get_tables(self) -> list:
        print(f"    [MCP Client] get_tables")
        result = self._call("get_tables", {})
        return eval(result)

    def get_table_schema(self, table_name: str) -> list:
        print(f"    [MCP Client] get_table_schema: {table_name}")
        result = self._call("get_table_schema", {"table_name": table_name})
        return eval(result)

    def get_row_count(self, table_name: str) -> int:
        print(f"    [MCP Client] get_row_count: {table_name}")
        result = self._call("get_row_count", {"table_name": table_name})
        if "ERROR" in str(result):
            return 0
        return int(result)

    def get_roles(self) -> list:
        print(f"    [MCP Client] get_roles")
        result = self._call("get_roles", {})
        return eval(result)


mcp_postgres = MCPPostgresClient()