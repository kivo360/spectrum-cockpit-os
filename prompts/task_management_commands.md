# Task Management Command Templates

Interactive prompts for common task management operations using the storage system.

## Quick Task Creation

**Command:** `create_task`

### Minimal Task (Simple)
```markdown
CREATE TASK:
Name: [Your task name here]
Description: [Brief description of what needs to be done]
Guide: [How to implement this]
```

**Example:**
```markdown
CREATE TASK:
Name: Fix login button styling
Description: The login button on the homepage has incorrect padding and color scheme
Guide: Update CSS classes in login.css, change padding to 12px, use primary brand color
```

### Standard Task (Detailed)
```markdown
CREATE TASK:
Name: [Task name]
Description: [Detailed description]
Guide: [Step-by-step implementation]
Priority: [P0|P1|P2|P3]
Complexity: [SIMPLE|MODERATE|COMPLEX|EPIC]
Hours: [1-40]
Category: [Category name]
Files:
  - path/to/file.ext [TO_MODIFY|CREATE|REFERENCE] - Description
  - path/to/another.ext [TYPE] - Description
Dependencies:
  - [Task UUID or Name]
```

**Example:**
```markdown
CREATE TASK:
Name: Add user profile image upload
Description: Allow users to upload and display profile images with automatic resizing and format validation
Guide: 1. Add file upload endpoint, 2. Implement image processing, 3. Update user model, 4. Create frontend component
Priority: P1
Complexity: MODERATE
Hours: 6
Category: Backend
Files:
  - src/api/upload.py [CREATE] - File upload endpoint
  - src/models/user.py [TO_MODIFY] - Add profile_image field
  - frontend/ProfileUpload.tsx [CREATE] - Upload component
Dependencies:
  - User authentication system
```

## Task Status Updates

**Command:** `update_task_status`

### Status Change
```markdown
UPDATE STATUS:
Task: [Task ID or Name]
Status: [PENDING|IN_PROGRESS|COMPLETED|BLOCKED] 
Reason: [Optional explanation]
```

**Examples:**
```markdown
UPDATE STATUS:
Task: Fix login button styling
Status: IN_PROGRESS
Reason: Started working on CSS updates

UPDATE STATUS:
Task: add-user-profile-upload-uuid-here
Status: BLOCKED
Reason: Waiting for S3 bucket configuration from DevOps team
```

## Task Queries and Search

**Command:** `find_tasks`

### Query by Status
```markdown
FIND TASKS:
Status: [PENDING|IN_PROGRESS|COMPLETED|BLOCKED]
Limit: [Optional number]
```

### Query by Multiple Criteria
```markdown
FIND TASKS:
Status: [Status]
Priority: [P0|P1|P2|P3]
Category: [Category name]
Complexity: [SIMPLE|MODERATE|COMPLEX|EPIC]
Created: [after|before] [YYYY-MM-DD]
```

**Examples:**
```markdown
FIND TASKS:
Status: PENDING
Priority: P1
Category: Backend

FIND TASKS:
Status: IN_PROGRESS
Created: after 2024-01-01
```

## Dependency Management

**Command:** `manage_dependencies`

### Add Dependency
```markdown
ADD DEPENDENCY:
Task: [Task ID or Name]
Depends on: [Dependency Task ID or Name]
```

### View Dependencies
```markdown
SHOW DEPENDENCIES:
Task: [Task ID or Name]
Direction: [dependencies|dependents|both]
```

**Examples:**
```markdown
ADD DEPENDENCY:
Task: Add user profile upload
Depends on: User authentication system

SHOW DEPENDENCIES:
Task: user-auth-uuid-here
Direction: dependents
```

## Batch Operations

**Command:** `batch_operation`

### Create Multiple Related Tasks
```markdown
BATCH CREATE:
Project: [Project/Feature name]
Tasks:
  - Name: [Task 1] | Priority: [P1] | Hours: [4] | Type: [SIMPLE]
  - Name: [Task 2] | Priority: [P1] | Hours: [6] | Type: [MODERATE]
  - Name: [Task 3] | Priority: [P2] | Hours: [8] | Type: [COMPLEX]
Dependencies:
  - Task 2 depends on Task 1
  - Task 3 depends on Task 2
```

**Example:**
```markdown
BATCH CREATE:
Project: User Dashboard Redesign
Tasks:
  - Name: Design new dashboard layout | Priority: P1 | Hours: 4 | Type: SIMPLE
  - Name: Implement dashboard components | Priority: P1 | Hours: 8 | Type: MODERATE  
  - Name: Add dashboard analytics | Priority: P2 | Hours: 6 | Type: MODERATE
Dependencies:
  - Implement dashboard components depends on Design new dashboard layout
  - Add dashboard analytics depends on Implement dashboard components
```

### Update Multiple Tasks
```markdown
BATCH UPDATE:
Filter: [Status/Priority/Category criteria]
Update:
  Status: [New status]
  Priority: [New priority]
  Category: [New category]
```

## Project Planning

**Command:** `plan_project`

### Sprint Planning
```markdown
PLAN SPRINT:
Duration: [1-4 weeks]
Capacity: [total hours available]
Priority: [minimum priority level]
Include:
  - Status: [PENDING|IN_PROGRESS]
  - Category: [category filter]
  - Complexity: [max complexity]
Auto-schedule: [yes|no]
```

**Example:**
```markdown
PLAN SPRINT:
Duration: 2 weeks
Capacity: 80 hours
Priority: P2
Include:
  - Status: PENDING
  - Category: Backend,Frontend
  - Complexity: COMPLEX
Auto-schedule: yes
```

### Dependency Analysis
```markdown
ANALYZE DEPENDENCIES:
Scope: [all|category|status]
Find: [cycles|critical_path|bottlenecks]
Format: [graph|list|summary]
```

## Reporting Commands

**Command:** `generate_report`

### Status Report
```markdown
STATUS REPORT:
Period: [last_week|last_month|current_sprint]
Include:
  - Summary: [task counts by status]
  - Details: [completed tasks]
  - Blocked: [blocked tasks with reasons]
  - Upcoming: [next priority tasks]
```

### Velocity Report
```markdown
VELOCITY REPORT:
Period: [weeks|months] [number]
Metrics:
  - Completion rate
  - Average task complexity
  - Time estimates vs actual
  - Category breakdown
```

## Advanced Operations

**Command:** `smart_suggestions`

### Task Breakdown
```markdown
SUGGEST BREAKDOWN:
Task: [Task ID or Name]
Max complexity: [SIMPLE|MODERATE|COMPLEX]
Target hours: [hours per subtask]
```

### Next Tasks
```markdown
SUGGEST NEXT:
Context: [current sprint|available capacity|dependencies]
Priority: [minimum priority]
Skills: [skill areas or categories]
```

**Examples:**
```markdown
SUGGEST BREAKDOWN:
Task: Redesign user dashboard
Max complexity: MODERATE
Target hours: 6

SUGGEST NEXT:
Context: available capacity
Priority: P1
Skills: Backend,API
```

## Quick Reference

### Status Values
- `PENDING` - Not started
- `IN_PROGRESS` - Currently being worked on  
- `COMPLETED` - Finished and verified
- `BLOCKED` - Waiting on dependencies

### Priority Levels
- `P0` - Critical (urgent, blocks other work)
- `P1` - High (important features)
- `P2` - Medium (standard work)
- `P3` - Low (nice-to-have)

### Complexity Levels
- `SIMPLE` - 1-4 hours
- `MODERATE` - 4-8 hours  
- `COMPLEX` - 8-16 hours
- `EPIC` - 16+ hours (consider breaking down)

### File Types
- `TO_MODIFY` - Existing file to change
- `CREATE` - New file to create
- `REFERENCE` - Existing file to consult
- `DEPENDENCY` - File this task depends on
- `OTHER` - Other relationship type