# Technical Stack

> Last Updated: 2025-07-31
> Version: 1.0.0

## Core Application Framework

- **Application Framework:** Python 3.12+ with FastMCP framework
- **Protocol Implementation:** Model Context Protocol (MCP) for AI agent communication
- **Async Framework:** asyncio for concurrent task processing and real-time updates
- **Schema Validation:** Pydantic v2 for robust data modeling and API validation
- **Configuration Management:** python-dotenv for environment-based configuration

## Database and Storage

- **Database System:** JSON file-based storage with automatic backup rotation
- **Primary Storage:** tasks.json with structured schema validation
- **Backup Strategy:** Timestamped backup files (tasks_backup_YYYY-MM-DD-HH-MM-SS.json)
- **Data Validation:** Pydantic models with comprehensive field validation
- **Migration System:** Schema versioning with automatic upgrade paths

## Frontend and User Interface

- **JavaScript Framework:** React 19 with TypeScript for type safety
- **Build System:** Vite for fast development and optimized production builds
- **Table Management:** TanStack React Table v8 for advanced data grid functionality
- **Data Visualization:** D3.js v7 for interactive dependency graph visualization
- **State Management:** React Context + useReducer for application state
- **Styling Framework:** Tailwind CSS for consistent design system

## Web Server and API

- **Embedded Server:** Python HTTP server with FastAPI integration
- **Static File Serving:** Built-in static file handler for embedded WebGUI
- **Real-Time Communication:** Server-Sent Events (SSE) for live updates
- **API Design:** RESTful endpoints following OpenAPI 3.0 specification
- **CORS Support:** Configurable cross-origin resource sharing for development

## Communication and Protocols

- **Primary Protocol:** Model Context Protocol (MCP) over stdio and SSE transports
- **Real-Time Updates:** Server-Sent Events (SSE) for live task status updates
- **Transport Layer:** Dual support for stdio (CLI integration) and HTTP/SSE (web clients)
- **Message Format:** JSON-based request/response with structured error handling
- **Client Support:** Cursor IDE, Claude Desktop, and custom MCP clients

## Development and Build Tools

- **Package Management:** uv for fast Python dependency management
- **Code Quality:** ruff for linting and formatting, mypy for type checking
- **Testing Framework:** pytest with asyncio support and comprehensive test coverage
- **Documentation:** Sphinx for API documentation, Markdown for user guides
- **Version Control:** Git with conventional commits and semantic versioning

## UI Component Libraries and Assets

- **Component Library:** Headless UI for accessible React components
- **Icon Library:** Heroicons for consistent iconography
- **Fonts Provider:** System fonts with fallback to web fonts
- **CSS Framework:** Tailwind CSS with custom design tokens
- **Animation Library:** Framer Motion for smooth transitions and interactions

## Deployment and Infrastructure

- **Application Hosting:** Local deployment with Docker containerization support
- **Asset Hosting:** Local file system with CDN support for production
- **Process Management:** systemd or Docker Compose for service orchestration
- **Monitoring:** Built-in health checks and performance metrics
- **Logging:** Structured logging with configurable levels and outputs

## Development Environment

- **Code Repository:** Git with GitHub for collaboration and issue tracking
- **IDE Integration:** Cursor IDE with MCP client support for development
- **Local Development:** Hot reloading for both Python backend and React frontend
- **Testing Environment:** Isolated test data with automatic cleanup
- **CI/CD Pipeline:** GitHub Actions for automated testing and deployment

## Security and Performance

- **Input Validation:** Comprehensive Pydantic schema validation for all inputs
- **Error Handling:** Structured error responses with user-friendly messages
- **Performance Optimization:** Async processing, connection pooling, and caching
- **Security Headers:** Standard HTTP security headers for web interface
- **Data Protection:** Local file-based storage with backup encryption options

## Import Strategy and Module Management

- **Import Strategy:** ES modules with dynamic imports for code splitting
- **Module Bundling:** Vite with tree shaking for optimized bundle sizes
- **Dependency Management:** npm for frontend, uv for Python backend
- **Type Definitions:** TypeScript definitions for all modules and APIs
- **Code Organization:** Domain-driven structure with clear separation of concerns

## Integration Points

- **MCP Clients:** Direct integration with Cursor IDE, Claude Desktop
- **File System:** Native file operations with path validation and security checks
- **External APIs:** Extensible plugin system for third-party integrations
- **Webhook Support:** Outbound notifications for external system integration
- **CLI Tools:** Command-line interface for headless operation and automation

## Configuration Management

- **Environment Variables:** Comprehensive configuration via .env files
- **Runtime Configuration:** Dynamic configuration updates without restart
- **Profile Management:** Multi-project configuration with inheritance
- **Feature Flags:** Runtime feature toggles for gradual rollout
- **Logging Configuration:** Configurable log levels and output destinations

## Performance and Scalability

- **Concurrency Model:** asyncio for handling multiple concurrent operations
- **Memory Management:** Efficient data structures and garbage collection tuning
- **Caching Strategy:** In-memory caching for frequently accessed data
- **Batch Processing:** Bulk operations for improved performance
- **Connection Pooling:** Efficient resource management for web connections

## Quality Assurance

- **Testing Strategy:** Unit tests, integration tests, and end-to-end testing
- **Code Coverage:** 90%+ test coverage requirement with branch coverage
- **Static Analysis:** Comprehensive linting and type checking
- **Performance Testing:** Load testing for concurrent user scenarios  
- **Security Scanning:** Automated vulnerability scanning for dependencies