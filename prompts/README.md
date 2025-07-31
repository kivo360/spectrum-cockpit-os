# Project Management Prompt Templates

This directory contains structured Markdown form-based prompts for efficient task and project management, inspired by agentOS instruction patterns.

## Overview

These templates provide consistent, structured approaches to common project management activities using our storage abstraction system. Each template is designed to work with both human users and AI agents for maximum flexibility.

## Template Files

### 📝 [task_creation_form.md](./task_creation_form.md)
Comprehensive form for creating well-structured tasks with full validation and metadata.

**Use Cases:**
- Creating new tasks with complete information
- Ensuring consistent task structure
- Validating task complexity and effort alignment
- Capturing all necessary metadata

**Key Features:**
- Built-in validation checklist
- Complexity-hours alignment guidance
- Comprehensive file relationship tracking
- Example complete task for reference

### ⚡ [task_management_commands.md](./task_management_commands.md)
Quick command templates for common task operations and queries.

**Use Cases:**
- Rapid task status updates
- Batch operations on multiple tasks
- Dependency management
- Project reporting and analysis

**Key Features:**
- Minimal and detailed task creation formats
- Status update commands
- Advanced query capabilities
- Batch operation templates

### 🏗️ [project_workflow_templates.md](./project_workflow_templates.md)
Structured workflows for project planning, feature development, and release management.

**Use Cases:**
- Epic planning and breakdown
- Sprint planning and execution
- Feature development lifecycle
- Bug fix workflows
- Release planning and retrospectives

**Key Features:**
- End-to-end workflow templates
- Capacity planning tools
- Risk assessment frameworks
- Communication and rollout strategies

## Quick Start Guide

### For New Users

1. **Start with Task Creation**: Use `task_creation_form.md` for your first few tasks to understand the full structure
2. **Switch to Commands**: Once familiar, use `task_management_commands.md` for faster operations
3. **Scale to Projects**: Use `project_workflow_templates.md` for larger initiatives

### For AI Agents

```markdown
AGENT INSTRUCTIONS:
1. Use task_creation_form.md structure for comprehensive task creation
2. Reference task_management_commands.md for operation syntax
3. Apply project_workflow_templates.md for multi-task planning
4. Always validate inputs against the built-in checklists
5. Suggest template improvements based on usage patterns
```

## Template Categories

### 🎯 Task Level
- **Individual Task Creation** - Single focused work items
- **Task Status Management** - Updates and transitions
- **Task Queries** - Finding and filtering tasks

### 📊 Project Level  
- **Sprint Planning** - Short-term iteration planning
- **Feature Development** - Medium-term feature delivery
- **Epic Planning** - Large-term initiative breakdown

### 🔄 Process Level
- **Bug Fix Workflows** - Systematic issue resolution
- **Release Planning** - Deployment and rollout processes
- **Retrospectives** - Learning and improvement cycles

## Integration with Storage System

These templates are designed to work seamlessly with our abstract storage interfaces:

### Graph Storage Integration
```markdown
# Dependencies are tracked in NetworkX graphs
ADD DEPENDENCY:
Task: implement-user-auth
Depends on: database-setup-complete
```

### Table Storage Integration  
```markdown
# Tasks are stored with full metadata in DuckDB
FIND TASKS:
Status: IN_PROGRESS
Priority: P1
Category: Backend
```

## Template Customization

### Adding Custom Fields

1. **Extend the Task Model**: Add new fields to `src/models/task.py`
2. **Update Templates**: Add corresponding form fields in templates
3. **Update Validation**: Add validation rules as needed

### Creating New Templates

1. **Follow the Pattern**: Use existing templates as structure guides
2. **Include Examples**: Always provide concrete examples
3. **Add Validation**: Include checklists and validation steps
4. **Test with Storage**: Ensure templates work with our storage abstractions

## Best Practices

### 🎯 Task Creation
- **Start Small**: Begin with simple tasks and grow complexity gradually
- **Be Specific**: Use concrete, actionable language
- **Align Effort**: Ensure complexity levels match estimated hours
- **Track Dependencies**: Always identify prerequisite tasks

### 📈 Project Planning
- **Break Down Epics**: Keep individual tasks under 16 hours
- **Plan Incrementally**: Use our proven "Start Small → Validate → Expand → Scale" methodology
- **Buffer Time**: Include 20-30% buffer for unexpected work
- **Track Velocity**: Monitor team capacity and completion rates

### 🔄 Process Management
- **Regular Reviews**: Use retrospective templates consistently
- **Update Status**: Keep task status current and accurate
- **Communicate Early**: Use templates to structure team communication
- **Document Decisions**: Capture rationale in task notes

## Advanced Usage

### Template Chaining
```markdown
WORKFLOW: Epic → Sprint → Tasks → Status Updates → Retrospective
1. Use Epic Planning Template
2. Break into Sprint Planning Template  
3. Create individual tasks with Task Creation Form
4. Manage with Task Management Commands
5. Review with Retrospective Template
```

### Automation Integration
```markdown
AUTOMATION HOOKS:
- Task creation triggers graph node creation
- Status updates trigger notification workflows
- Dependency changes trigger re-scheduling
- Completion triggers downstream task activation
```

### Reporting Integration
```markdown
REPORTING QUERIES:
- Sprint velocity from completed tasks
- Blocked tasks with dependency analysis
- Category-based workload distribution
- Individual contributor performance metrics
```

## Contributing

### Template Improvements
1. **Identify Gaps**: Find missing use cases or workflows
2. **Propose Changes**: Use GitHub issues for template suggestions
3. **Test Thoroughly**: Validate with real projects before submitting
4. **Update Documentation**: Keep this README current

### Validation Rules
1. **Required Fields**: Mark all required template fields clearly
2. **Format Consistency**: Follow established Markdown patterns
3. **Example Quality**: Provide realistic, detailed examples
4. **Cross-References**: Link related templates and concepts

## Support

For questions about these templates:

1. **Template Issues**: Check existing GitHub issues for similar questions
2. **Usage Examples**: Review the `example_usage.py` file for integration patterns
3. **Storage Questions**: See the storage abstraction documentation
4. **Process Questions**: Use retrospective templates to identify improvement needs

---

**Version**: 1.0  
**Last Updated**: 2024-01-31  
**Compatible With**: MCP Task Manager Storage System v1.0