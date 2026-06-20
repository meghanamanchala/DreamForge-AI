import inspect
from pydantic import BaseModel

class MCPToolRegistry:
    def __init__(self):
        self.tools = {}

    def register(self, name=None, description=None, input_schema=None):
        """
        Decorator to register a tool in the MCP registry.
        :param name: Optional override name for the tool.
        :param description: Optional override description.
        :param input_schema: A Pydantic BaseModel class defining inputs.
        """
        def decorator(func):
            tool_name = name or func.__name__
            tool_desc = description or func.__doc__ or "No description provided."
            
            # Compile inputSchema in MCP format
            schema = {
                "type": "object",
                "properties": {},
                "required": []
            }
            if input_schema and issubclass(input_schema, BaseModel):
                pydantic_schema = input_schema.model_json_schema()
                # Remove title keys added by Pydantic (not standard in clean MCP schema)
                pydantic_schema.pop("title", None)
                if "properties" in pydantic_schema:
                    for prop in pydantic_schema["properties"].values():
                        prop.pop("title", None)
                schema = pydantic_schema
            
            self.tools[tool_name] = {
                "name": tool_name,
                "description": tool_desc.strip(),
                "inputSchema": schema,
                "func": func
            }
            return func
        return decorator

    def get_mcp_schemas(self):
        """Returns the list of tool definitions in MCP-compliant JSON schema format."""
        return [
            {
                "name": t["name"],
                "description": t["description"],
                "inputSchema": t["inputSchema"]
            }
            for t in self.tools.values()
        ]

    def execute_tool(self, name, arguments):
        """Executes a registered tool using a dictionary of inputs."""
        if name not in self.tools:
            raise ValueError(f"Tool {name} is not registered in the MCP registry.")
        return self.tools[name]["func"](**arguments)

# Global Registry instance
mcp_registry = MCPToolRegistry()
