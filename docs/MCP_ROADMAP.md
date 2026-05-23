# MCP Roadmap

MCP is planned for Centroid v0.5.0 and is not implemented in the v0.4.x provider-adapter release line.

MCP is an interoperability boundary, not a model provider. The provider-adapter layer may record remote-MCP capability metadata for providers, but it does not create an MCP client, MCP server, remote MCP session, or any MCP tool execution path.

Initial future MCP work should expose read-only or proposal-only Centroid capabilities first. Mutating execution should remain deferred, explicit, audited, safety evaluated, and approval-gated.
