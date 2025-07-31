# MCP Shrimp Task Manager - Visual Documentation & Diagrams

**Repository**: https://github.com/cjo4m06/mcp-shrimp-task-manager  
**Documentation Date**: 2025-07-31  

## Complete System Architecture Diagrams

### High-Level System Architecture
Multi-layered architecture showing AI client integration with the MCP server and core application components:

```mermaid
graph TB
    subgraph "AI Client Layer"
        aiClients["AI Clients\n(Cursor IDE, Claude Desktop)"]
    end
    
    subgraph "MCP Protocol Layer"
        mcpServer["MCP Server\nsrc/index.ts"]
    end
    
    subgraph "Core Application Layer"
        taskEngine["Task Management Engine\nsrc/tools/"]
        promptSystem["Prompt System\nsrc/prompts/"]
        dataLayer["Data Layer"]
    end
    
    subgraph "User Interface Layer"
        embeddedGUI["Embedded WebGUI\nsrc/public/"]
        standaloneViewer["Standalone Task Viewer\ntools/task-viewer/"]
    end
    
    subgraph "Data Storage"
        primaryStorage["tasks.json"]
        backupStorage["tasks_backup_*.json"]
    end
    
    aiClients --> mcpServer
    mcpServer --> taskEngine
    mcpServer --> promptSystem
    taskEngine --> dataLayer
    promptSystem --> dataLayer
    dataLayer --> primaryStorage
    dataLayer --> backupStorage
    
    embeddedGUI --> primaryStorage
    standaloneViewer --> primaryStorage
```

### Core MCP Server Integration
Detailed view of MCP SDK integration with task management tools:

```mermaid
graph TD
    subgraph "MCP SDK Integration"
        mcpSDK["MCP SDK Import"]
        serverInstance["Server Instance"]
        toolHandlers["Tool Handlers"]
    end
    
    subgraph "Task Management Tools"
        planTask["planTask()"]
        analyzeTask["analyzeTask()"]
        reflectTask["reflectTask()"]
        splitTasks["splitTasks()"]
        executeTask["executeTask()"]
        verifyTask["verifyTask()"]
        listTasks["listTasks()"]
        queryTask["queryTask()"]
        deleteTask["deleteTask()"]
        processThought["processThought()"]
        researchMode["researchMode()"]
        initProjectRules["initProjectRules()"]
    end
    
    subgraph "Data Operations"
        taskModel["Task Model"]
        fileOps["File Operations"]
        dataValidation["Data Validation"]
    end
    
    mcpSDK --> serverInstance
    serverInstance --> toolHandlers
    toolHandlers --> planTask
    toolHandlers --> analyzeTask
    toolHandlers --> reflectTask
    toolHandlers --> splitTasks
    toolHandlers --> executeTask
    toolHandlers --> verifyTask
    toolHandlers --> listTasks
    toolHandlers --> queryTask
    toolHandlers --> deleteTask
    toolHandlers --> processThought
    toolHandlers --> researchMode
    toolHandlers --> initProjectRules
    
    planTask --> taskModel
    analyzeTask --> taskModel
    splitTasks --> taskModel
    executeTask --> fileOps
    verifyTask --> dataValidation
```

### Integration Points and Data Persistence
How external systems integrate with core data operations:

```mermaid
graph TD
    subgraph "External Integration"
        fileSystem["File System"]
        ideClients["IDE Clients"]
        webBrowsers["Web Browsers"]
    end
    
    subgraph "Core Data Operations"
        taskCRUD["Task CRUD Operations"]
        dependencyMgmt["Dependency Management"]
        stateTransitions["State Transitions"]
        memoryArchival["Memory Archival"]
    end
    
    subgraph "Persistence Layer"
        primaryStorage["Primary Storage\ntasks.json"]
        backupStorage["Backup Storage\ntasks_backup_YYYY-MM-DD*.json"]
    end
    
    fileSystem --> taskCRUD
    ideClients --> taskCRUD
    webBrowsers --> taskCRUD
    
    taskCRUD --> dependencyMgmt
    taskCRUD --> stateTransitions
    taskCRUD --> memoryArchival
    
    dependencyMgmt --> primaryStorage
    stateTransitions --> primaryStorage
    memoryArchival --> backupStorage
```

## Task Workflow and Lifecycle Diagrams

### Task Data Flow and State Management
Complete pipeline from natural language input to task execution:

```mermaid
graph TD
    subgraph "Input Processing"
        naturalLang["Natural Language Input"]
        aiAgent["AI Agent Processing"]
        mcpToolCalls["MCP Tool Calls"]
    end
    
    subgraph "Task Processing Pipeline"
        taskPlanning["Task Planning\nplan_task"]
        taskAnalysis["Task Analysis\nanalyze_task"]
        taskReflection["Task Reflection\nreflect_task"]
        taskSplitting["Task Splitting\nsplit_tasks"]
        taskExecution["Task Execution\nexecute_task"]
        taskVerification["Task Verification\nverify_task"]
    end
    
    subgraph "State Management"
        pending["PENDING"]
        inProgress["IN_PROGRESS"]
        completed["COMPLETED"]
        blocked["BLOCKED"]
    end
    
    subgraph "Persistence"
        activeTasks["Active Tasks\ntasks.json"]
        memoryBackup["Memory Backup\ntasks_backup_*.json"]
    end
    
    naturalLang --> aiAgent
    aiAgent --> mcpToolCalls
    mcpToolCalls --> taskPlanning
    taskPlanning --> taskAnalysis
    taskAnalysis --> taskReflection
    taskReflection --> taskSplitting
    taskSplitting --> activeTasks
    
    activeTasks --> pending
    pending --> taskExecution
    taskExecution --> inProgress
    inProgress --> taskVerification
    taskVerification --> completed
    inProgress --> blocked
    blocked --> pending
    
    activeTasks --> memoryBackup
    completed --> memoryBackup
```

### Configuration and Template Processing Flow
How configuration and templates generate dynamic prompts:

```mermaid
graph TD
    subgraph "Configuration Sources"
        envVars["Environment Variables\nMCP_PROMPT_*"]
        mcpConfig["MCP Configuration"]
    end
    
    subgraph "Template Processing"
        templateEngine["Template Engine"]
        paramInjection["Parameter Injection"]
        promptGenerators["Prompt Generators"]
    end
    
    subgraph "Output"
        aiAgentPrompts["AI Agent Prompts"]
    end
    
    envVars --> promptGenerators
    mcpConfig --> promptGenerators
    promptGenerators --> templateEngine
    templateEngine --> paramInjection
    paramInjection --> aiAgentPrompts
```

## Agent Coordination and Workflow Diagrams

### AI Agent Integration Layer
How TaskPlanner and TaskExecutor modes interact with core workflow tools:

```mermaid
graph TD
    subgraph "AI Agent Modes"
        taskPlanner["TaskPlanner Mode\nPlanning & Analysis Only"]
        taskExecutor["TaskExecutor Mode\nImplementation & Verification"]
    end
    
    subgraph "Planning Tools"
        planTask["plan_task\ngetPlanTaskPrompt()"]
        analyzeTask["analyze_task\ngetAnalyzeTaskPrompt()"]
        reflectTask["reflect_task\ngetReflectTaskPrompt()"]
        splitTasksRaw["split_tasks\nTask Decomposition"]
        initRules["init_project_rules\nProject Standards"]
        researchMode["research_mode\nSystematic Investigation"]
    end
    
    subgraph "Execution Tools"
        executeTask["execute_task\ngetExecuteTaskPrompt()"]
        verifyTask["verify_task\ngetVerifyTaskPrompt()"]
        updateTask["update_task\nContent Updates"]
    end
    
    subgraph "Shared Tools"
        listTasks["list_tasks\nTask Overview"]
        queryTask["query_task\nTask Search"]
        getDetail["get_task_detail\nDetailed Information"]
    end
    
    taskPlanner --> planTask
    taskPlanner --> analyzeTask
    taskPlanner --> reflectTask
    taskPlanner --> splitTasksRaw
    taskPlanner --> initRules
    taskPlanner --> researchMode
    
    taskExecutor --> executeTask
    taskExecutor --> verifyTask
    taskExecutor --> updateTask
    
    taskPlanner --> listTasks
    taskPlanner --> queryTask
    taskPlanner --> getDetail
    taskExecutor --> listTasks
    taskExecutor --> queryTask
    taskExecutor --> getDetail
```

### Multi-Agent Coordination Sequence
Complete project lifecycle with agent handoffs:

```mermaid
sequenceDiagram
    participant User
    participant TaskPlanner
    participant MCP_Server
    participant TaskStorage
    participant TaskExecutor
    participant WebGUI
    
    User->>TaskPlanner: Natural language requirements
    TaskPlanner->>MCP_Server: plan_task(requirements)
    MCP_Server->>TaskPlanner: Initial task concept
    
    TaskPlanner->>MCP_Server: analyze_task(concept)
    MCP_Server->>TaskPlanner: Detailed analysis result
    
    TaskPlanner->>MCP_Server: reflect_task(analysis)
    MCP_Server->>TaskPlanner: Validated solution approach
    
    TaskPlanner->>MCP_Server: split_tasks(validated_solution)
    MCP_Server->>TaskStorage: Store structured tasks with dependencies
    TaskStorage-->>MCP_Server: Task IDs and dependency graph
    TaskStorage-->>WebGUI: Real-time task updates via SSE
    
    Note over MCP_Server: Dependency resolution and execution ordering
    
    TaskExecutor->>MCP_Server: list_tasks()
    MCP_Server->>TaskExecutor: Available executable tasks
    
    loop For each ready task
        TaskExecutor->>MCP_Server: execute_task(taskId)
        MCP_Server->>TaskStorage: Update status to IN_PROGRESS
        TaskStorage-->>WebGUI: Status update notification
        
        TaskExecutor->>MCP_Server: verify_task(taskId)
        MCP_Server->>TaskStorage: Mark as COMPLETED
        TaskStorage-->>WebGUI: Completion notification
        
        Note over TaskStorage: Check if dependent tasks become ready
    end
    
    TaskStorage-->>User: Project completion summary
    WebGUI-->>User: Visual progress dashboard
```

## Web Interface Architecture and Components

### Web Interface Component Architecture
Dual interface system with embedded and standalone components:

```mermaid
graph TD
    subgraph "HTTP Server Layer"
        expressServer["Express Server\nsrc/web/webServer.ts"]
        apiEndpoints["API Endpoints\n/api/tasks, /api/profiles"]
        sseStream["SSE Stream\n/events"]
        staticFiles["Static Files\nsrc/public/"]
    end
    
    subgraph "Embedded WebGUI"
        direction TB
        embeddedHTML["Embedded HTML\nsrc/public/index.html"]
        d3Visualization["D3.js Dependency Graph\nsrc/public/script.js"]
        taskTable["Task Table Component"]
        filterSystem["Filter & Search System"]
    end
    
    subgraph "Standalone Task Viewer"
        direction TB
        reactApp["React 19 + Vite App\ntools/task-viewer/"]
        tanStackTable["TanStack React Table"]
        profileManager["Profile Manager"]
        dragDropTabs["Drag & Drop Tabs"]
        autoRefresh["Auto-refresh System"]
    end
    
    subgraph "Data Sources"
        tasksData["Tasks Data\ntasks.json"]
        profileData["Profile Data\nper-profile tasks"]
    end
    
    expressServer --> apiEndpoints
    expressServer --> sseStream
    expressServer --> staticFiles
    
    staticFiles --> embeddedHTML
    embeddedHTML --> d3Visualization
    embeddedHTML --> taskTable
    embeddedHTML --> filterSystem
    
    apiEndpoints --> reactApp
    reactApp --> tanStackTable
    reactApp --> profileManager
    reactApp --> dragDropTabs
    reactApp --> autoRefresh
    
    d3Visualization --> tasksData
    taskTable --> tasksData
    tanStackTable --> tasksData
    profileManager --> profileData
    
    sseStream --> embeddedHTML
    sseStream --> reactApp
```

### Dependency Graph Visualization
D3.js-based interactive dependency graph with status-based coloring:

```mermaid
graph TD
    subgraph "Graph Components"
        nodes["Task Nodes\n• Status-based colors\n• Interactive hover\n• Click for details"]
        edges["Dependency Edges\n• Directional arrows\n• Relationship lines"]
        legend["Status Legend\n• PENDING: Gray\n• IN_PROGRESS: Blue\n• COMPLETED: Green\n• BLOCKED: Red"]
    end
    
    subgraph "Interactive Features"
        forceSimulation["D3 Force Simulation\n• Node positioning\n• Edge tension\n• Collision detection"]
        zoomPan["Zoom & Pan Controls"]
        filtering["Task Filtering\n• By status\n• By name\n• By dependencies"]
    end
    
    subgraph "Real-time Updates"
        sseUpdates["SSE Task Updates"]
        graphRefresh["Auto Graph Refresh"]
        statusAnimation["Status Change Animation"]
    end
    
    nodes --> forceSimulation
    edges --> forceSimulation
    forceSimulation --> zoomPan
    
    sseUpdates --> graphRefresh
    graphRefresh --> statusAnimation
    statusAnimation --> nodes
```

## Task State and Lifecycle Diagrams

### Task State Machine
Complete state transitions with conditions:

```mermaid
stateDiagram-v2
    [*] --> PENDING : Task Created
    
    PENDING --> IN_PROGRESS : execute_task() called
    PENDING --> BLOCKED : Dependencies not met
    
    IN_PROGRESS --> COMPLETED : verify_task() success
    IN_PROGRESS --> BLOCKED : External blocker encountered
    IN_PROGRESS --> PENDING : Task reset/retry
    
    BLOCKED --> PENDING : Dependencies resolved
    BLOCKED --> BLOCKED : Still waiting
    
    COMPLETED --> [*] : Task finished
    
    note right of PENDING
        Ready for execution
        All dependencies met
    end note
    
    note right of IN_PROGRESS
        Currently being executed
        Agent actively working
    end note
    
    note right of COMPLETED
        Successfully finished
        Verification passed
    end note
    
    note right of BLOCKED
        Cannot proceed
        Waiting for dependencies
        or external factors
    end note
```

### Task Dependency Resolution Flow
How the system resolves and manages task dependencies:

```mermaid
flowchart TD
    A[New Task with Dependencies] --> B{Dependency Format Check}
    
    B -->|UUID Format| C[Check Task Exists by ID]
    B -->|Name Format| D[Lookup in Name-to-ID Map]
    
    C -->|Exists| E[Add to Resolved Dependencies]
    C -->|Not Found| F[Skip with Warning]
    
    D -->|Found| G[Get Task ID]
    D -->|Not Found| F
    
    G --> H[Check Task Exists by ID]
    H -->|Exists| E
    H -->|Not Found| F
    
    E --> I{More Dependencies?}
    F --> I
    
    I -->|Yes| B
    I -->|No| J[Create Task with Resolved Dependencies]
    
    J --> K[Update Dependency Graph]
    K --> L[Calculate Execution Order]
    L --> M[Mark Ready Tasks as PENDING]
    M --> N[Mark Blocked Tasks as BLOCKED]
```

## System Integration Patterns

### MCP Protocol Communication Flow
How external clients communicate with the MCP server:

```mermaid
sequenceDiagram
    participant Client as AI Client
    participant Transport as MCP Transport
    participant Server as MCP Server
    participant Handler as Tool Handler
    participant Storage as Task Storage
    
    Client->>Transport: MCP Request
    Transport->>Server: tools/call message
    Server->>Server: Validate tool name & schema
    Server->>Handler: Execute tool function
    Handler->>Storage: Data operations
    Storage-->>Handler: Results
    Handler-->>Server: Tool response
    Server-->>Transport: MCP Response
    Transport-->>Client: Results
    
    Note over Client,Storage: All communication via MCP protocol
    Note over Server: Schema validation with Zod
    Note over Storage: Atomic operations with backup
```

### Real-time Update Architecture
Server-Sent Events (SSE) for live updates:

```mermaid
graph TD
    subgraph "Update Sources"
        taskOps["Task Operations\n(CRUD)"]
        statusChanges["Status Changes"]
        dependencyUpdates["Dependency Updates"]
    end
    
    subgraph "SSE Server"
        eventStream["Event Stream\n/events endpoint"]
        clientConnections["Active Client Connections"]
        messageQueue["Message Queue"]
    end
    
    subgraph "Client Updates"
        embeddedGUI["Embedded WebGUI"]
        taskViewer["Standalone Task Viewer"]
        mobileClients["Mobile/External Clients"]
    end
    
    taskOps --> eventStream
    statusChanges --> eventStream
    dependencyUpdates --> eventStream
    
    eventStream --> messageQueue
    messageQueue --> clientConnections
    
    clientConnections --> embeddedGUI
    clientConnections --> taskViewer
    clientConnections --> mobileClients
    
    embeddedGUI --> |Auto-refresh graphs| embeddedGUI
    taskViewer --> |Update task tables| taskViewer
```

## Performance and Scalability Patterns

### Task Processing Optimization
How the system handles large task sets efficiently:

```mermaid
graph TD
    subgraph "Input Optimization"
        batchValidation["Batch Schema Validation"]
        nameUniqueness["Name Uniqueness Check"]
        sizeLimit["5000 Character Limit"]
    end
    
    subgraph "Processing Optimization"
        parallelResolution["Parallel Dependency Resolution"]
        bulkOperations["Bulk Database Operations"]
        transactional["Transactional Updates"]
    end
    
    subgraph "Storage Optimization"
        jsonBackup["Automatic JSON Backup"]
        incrementalUpdates["Incremental Updates"]
        memoryManagement["Memory Management"]
    end
    
    batchValidation --> parallelResolution
    nameUniqueness --> parallelResolution
    sizeLimit --> parallelResolution
    
    parallelResolution --> bulkOperations
    bulkOperations --> transactional
    
    transactional --> jsonBackup
    transactional --> incrementalUpdates
    transactional --> memoryManagement
```

This comprehensive visual documentation provides complete system understanding through diagrams covering architecture, workflows, agent coordination, web interfaces, state management, and integration patterns - enabling full comprehension of the sophisticated task management system.