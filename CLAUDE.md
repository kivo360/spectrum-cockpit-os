# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Server
```bash
# Using Python directly (SSE transport)
python src/main.py

# Using uv for dependency management
uv pip install -e .
python src/main.py

# Using Docker (recommended for production)
docker build -t task-manager-mcp .
docker run --env-file .env -p 8050:8050 task-manager-mcp
```

### Environment Setup
```bash
# Copy example environment file
cp .env.example .env

# Install dependencies
uv pip install -e .
# OR
pip install -e .
```

### Testing the Server
```bash
# Test MCP tools via SSE endpoint
curl http://localhost:8050/sse

# Test individual tools through MCP client integration
```

## Architecture Overview

### Core Components

**FastMCP Framework**: The server is built using the FastMCP library, which provides a simplified interface for creating MCP servers with automatic tool registration via the `@mcp.tool()` decorator.

**TaskManager Class**: Central class that handles all task management operations including:
- Markdown file parsing and generation
- Task and subtask status tracking
- PRD (Product Requirements Document) parsing
- File template generation

**File Storage**: Uses local filesystem storage with tasks stored as Markdown files in the `tasks/` directory. Each project gets its own `.md` file (e.g., `tasks/my-project.md`).

### Key Patterns

**Markdown-Based Task Format**: Tasks are stored in a structured Markdown format with:
- Task headers: `## Task: Title`
- Subtasks: `- [ ] Subtask` or `- [x] Completed`
- Categories: `[MVP]`, `[AI]`, `[UX]`, `[INFRA]`
- Priority levels: `P0` (critical) to `P3` (low)
- Complexity and time estimates

**AI-Powered Features**: Several tools include placeholder AI integration points for:
- Task expansion and subtask generation
- Complexity estimation
- Next action suggestions
- File template generation

**Dependency Tracking**: Tasks can reference dependencies by task number, enabling proper sequencing of work.

## MCP Integration

### Transport Modes
- **SSE (Server-Sent Events)**: Default mode for web-based clients
- **stdio**: For command-line MCP clients

### Configuration
The server supports both SSE and stdio transports, configured via environment variables:
- `TRANSPORT`: "sse" or "stdio"
- `HOST`: Server host (SSE only)  
- `PORT`: Server port (SSE only)

### Available Tools
The server exposes 10 MCP tools for task management:
- `create_task_file`: Initialize new project task files
- `add_task`: Add tasks with subtasks to projects
- `parse_prd`: Convert PRDs into structured task lists
- `update_task_status`: Mark tasks/subtasks as complete
- `get_next_task`: Find next uncompleted work
- `expand_task`: Break tasks into smaller subtasks
- `generate_task_file`: Create file templates from tasks
- `get_task_dependencies`: Track task relationships
- `estimate_task_complexity`: AI-powered complexity analysis
- `suggest_next_actions`: AI-powered next step recommendations

## Important Implementation Details

**File Path Handling**: All task files use the pattern `tasks/{project_name}.md` with automatic directory creation.

**Error Handling**: All tools include comprehensive try/catch blocks returning user-friendly error messages.

**Batch Operations**: The `add_task` tool supports batch mode for bulk task additions without file re-reading.

**Task Status Management**: Status updates work at both task and subtask levels with proper Markdown checkbox formatting.

**PRD Parsing Logic**: The `parse_prd` tool includes sophisticated parsing that creates structured tasks with categories, priorities, dependencies, and time estimates based on document sections.

## Agent OS Documentation

### Product Context
- **Mission & Vision:** @.agent-os/product/mission.md
- **Technical Architecture:** @.agent-os/product/tech-stack.md
- **Development Roadmap:** @.agent-os/product/roadmap.md
- **Decision History:** @.agent-os/product/decisions.md

### Development Standards
- **Code Style:** Follow Python PEP 8 with FastMCP patterns
- **Best Practices:** Comprehensive error handling, async/await patterns, Pydantic validation

### Project Management
- **Active Specs:** @.agent-os/specs/ (to be created for specific features)
- **Spec Planning:** Use `@~/.agent-os/instructions/create-spec.md`
- **Tasks Execution:** Use `@~/.agent-os/instructions/execute-tasks.md`

## Workflow Instructions

When asked to work on this codebase:

1. **First**, check @.agent-os/product/roadmap.md for current priorities
2. **Then**, follow the appropriate instruction file:
   - For new features: @.agent-os/instructions/create-spec.md
   - For tasks execution: @.agent-os/instructions/execute-tasks.md
3. **Always**, adhere to the standards in the files listed above

## Important Notes

- Product-specific files in `.agent-os/product/` override any global standards
- User's specific instructions override (or amend) instructions found in `.agent-os/specs/...`
- Always adhere to established patterns, code style, and best practices documented above.
- **Decision Authority**: @.agent-os/product/decisions.md has override priority for conflicts