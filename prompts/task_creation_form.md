# Task Creation Form

Use this form to create well-structured tasks for the project management system.

## Basic Information

**Task Name:** _[Required: 1-100 characters, clear and descriptive]_
```
Example: "Implement user authentication API endpoints"
```

**Description:** _[Required: Minimum 10 characters, detailed explanation]_
```
Provide a comprehensive description of what needs to be accomplished.
Include context, background, and the problem being solved.

Example: 
"Create secure authentication endpoints for user login, logout, and token refresh. 
This will enable the frontend application to authenticate users and maintain 
secure sessions. The implementation should support JWT tokens and include 
proper error handling for invalid credentials."
```

**Implementation Guide:** _[Required: Minimum 10 characters, step-by-step approach]_
```
Provide clear, actionable steps for implementing this task.
Include technical decisions, frameworks, and approaches.

Example:
"1. Set up FastAPI authentication dependencies
2. Create user login endpoint with password validation
3. Implement JWT token generation and validation
4. Add logout endpoint with token blacklisting
5. Create token refresh mechanism
6. Add comprehensive error handling and logging
7. Write unit and integration tests"
```

## Task Metadata

**Priority Level:** _[Select one: P0 (Critical), P1 (High), P2 (Medium), P3 (Low)]_
- [ ] P0 - Critical (blocks other work, urgent fixes)
- [ ] P1 - High (important features, significant impact)
- [x] P2 - Medium (standard features, moderate impact) ← Default
- [ ] P3 - Low (nice-to-have, minimal impact)

**Complexity Level:** _[Select one based on estimated effort]_
- [ ] SIMPLE (1-4 hours) - Quick fixes, simple features
- [ ] MODERATE (4-8 hours) - Standard features, moderate complexity
- [ ] COMPLEX (8-16 hours) - Advanced features, significant work
- [ ] EPIC (16+ hours) - Consider breaking into smaller tasks

**Estimated Hours:** _[Optional: 1-40 hours, should align with complexity]_
```
Enter estimated work hours (leave blank if uncertain):
_____ hours
```

**Category:** _[Optional: Max 50 characters, for organization]_
```
Examples: "Backend", "Frontend", "DevOps", "Testing", "Documentation"
```

## Dependencies and Files

**Task Dependencies:** _[List UUIDs of tasks that must be completed first]_
```
If this task depends on other tasks, list their IDs:
- Task ID: ________________________________________
- Task ID: ________________________________________
- Task ID: ________________________________________
```

**Related Files:** _[Files that will be created, modified, or referenced]_

### File 1
- **Path:** `_________________________________`
- **Type:** 
  - [ ] TO_MODIFY (existing file to change)
  - [ ] REFERENCE (existing file to consult)
  - [ ] CREATE (new file to create)
  - [ ] DEPENDENCY (file this task depends on)
  - [ ] OTHER (specify in description)
- **Description:** `_________________________________`
- **Line Range:** Start: `____` End: `____` _(optional, for specific sections)_

### File 2
- **Path:** `_________________________________`
- **Type:** 
  - [ ] TO_MODIFY (existing file to change)
  - [ ] REFERENCE (existing file to consult)
  - [ ] CREATE (new file to create)
  - [ ] DEPENDENCY (file this task depends on)
  - [ ] OTHER (specify in description)
- **Description:** `_________________________________`
- **Line Range:** Start: `____` End: `____` _(optional, for specific sections)_

## Verification and Quality

**Verification Criteria:** _[Optional: How to confirm task completion]_
```
Define clear, testable criteria for completion:

Example:
"✓ Authentication endpoints return proper HTTP status codes
✓ JWT tokens are generated with correct claims and expiration
✓ Invalid credentials return appropriate error messages
✓ All endpoints have comprehensive test coverage (>90%)
✓ API documentation is updated with new endpoints
✓ Security review passes with no critical findings"
```

**Additional Notes:** _[Optional: Any other relevant information]_
```
Include any additional context, constraints, or considerations:
- Technical constraints or requirements
- Business context or stakeholder needs
- Links to relevant documentation or resources
- Potential risks or considerations
```

## Task Status

**Initial Status:** _[Select starting status]_
- [x] PENDING (not yet started) ← Default
- [ ] IN_PROGRESS (actively being worked on)
- [ ] BLOCKED (waiting on dependencies)
- [ ] COMPLETED (finished and verified)

---

## Form Validation Checklist

Before submitting, ensure:
- [ ] Task name is clear and descriptive (1-100 chars)
- [ ] Description explains the problem and context (10+ chars)
- [ ] Implementation guide provides actionable steps (10+ chars)
- [ ] Priority level is selected appropriately
- [ ] Complexity level matches estimated hours
- [ ] Related files have clear descriptions
- [ ] Verification criteria are testable (if provided)

## Example Complete Task Form

```markdown
**Task Name:** Implement GraphQL API for Task Queries

**Description:** Create GraphQL endpoints to allow flexible querying of tasks with filtering, sorting, and pagination. This will replace the current REST endpoints for task retrieval and provide better performance for complex queries needed by the frontend dashboard.

**Implementation Guide:** 
1. Install and configure GraphQL dependencies (graphene-python)
2. Create GraphQL schema for Task model with all fields
3. Implement resolvers for task queries with filters (status, priority, category)
4. Add pagination support using cursor-based pagination
5. Create sorting capabilities for common fields (created_at, priority, name)
6. Add authentication middleware for GraphQL endpoints
7. Write comprehensive tests for all query scenarios
8. Update API documentation with GraphQL schema

**Priority Level:** P1 (High)
**Complexity Level:** COMPLEX (8-16 hours)
**Estimated Hours:** 12 hours
**Category:** Backend

**Related Files:**
- Path: `src/api/graphql_schema.py` | Type: CREATE | Description: GraphQL schema definitions
- Path: `src/api/resolvers.py` | Type: CREATE | Description: GraphQL query resolvers
- Path: `tests/api/test_graphql.py` | Type: CREATE | Description: GraphQL endpoint tests

**Verification Criteria:**
✓ GraphQL playground accessible at /graphql endpoint
✓ All task fields queryable with proper types
✓ Filtering works for status, priority, and category
✓ Pagination returns consistent results with cursors
✓ Sorting works for all specified fields
✓ Authentication properly protects endpoints
✓ Test coverage >95% for GraphQL functionality
```