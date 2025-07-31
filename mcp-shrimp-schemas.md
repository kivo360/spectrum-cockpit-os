# MCP Shrimp Task Manager - Complete Schemas Documentation

**Repository**: https://github.com/cjo4m06/mcp-shrimp-task-manager  
**Documentation Date**: 2025-07-31  

## Complete MCP Tool Schemas

The mcp-shrimp-task-manager uses Zod schemas for input validation across all 15 MCP tools. Here are the detailed schemas:

### Core Task Splitting Schema: `splitTasksRawSchema`

This is the most comprehensive schema, handling complex task decomposition:

```typescript
export const splitTasksRawSchema = z.object({
  updateMode: z
    .enum(["append", "overwrite", "selective", "clearAllTasks"])
    .describe(
      "任務更新模式選擇：'append'(保留所有現有任務並添加新任務)、'overwrite'(清除所有未完成任務並完全替換，保留已完成任務)、'selective'(智能更新：根據任務名稱匹配更新現有任務，保留不在列表中的任務，推薦用於任務微調)、'clearAllTasks'(清除所有任務並創建備份)。\n預設為'clearAllTasks'模式，只有用戶要求變更或修改計劃內容才使用其他模式"
    ),
  tasksRaw: z
    .string()
    .describe(
      "結構化的任務清單，每個任務應保持原子性且有明確的完成標準，避免過於簡單的任務，簡單修改可與其他任務整合，避免任務過多，範例：[{name: '簡潔明確的任務名稱，應能清晰表達任務目的', description: '詳細的任務描述，包含實施要點、技術細節和驗收標準', implementationGuide: '此特定任務的具體實現方法和步驟，請參考之前的分析結果提供精簡pseudocode', notes: '補充說明、特殊處理要求或實施建議（選填）', dependencies: ['此任務依賴的前置任務完整名稱'], relatedFiles: [{path: '文件路徑', type: '文件類型 (TO_MODIFY: 待修改, REFERENCE: 參考資料, CREATE: 待建立, DEPENDENCY: 依賴文件, OTHER: 其他)', description: '文件描述', lineStart: 1, lineEnd: 100}], verificationCriteria: '此特定任務的驗證標準和檢驗方法'}, ...]"
    ),
  globalAnalysisResult: z
    .string()
    .optional()
    .describe("任務最終目標，來自之前分析適用於所有任務的通用部分"),
});
```

### Individual Task Schema: `tasksSchema`

```typescript
const tasksSchema = z
  .array(
    z.object({
      name: z
        .string()
        .max(100, {
          message: "任務名稱過長，請限制在100個字符以內",
        })
        .describe("簡潔明確的任務名稱，應能清晰表達任務目的"),
      description: z
        .string()
        .min(10, {
          message: "任務描述過短，請提供更詳細的內容以確保理解",
        })
        .describe("詳細的任務描述，包含實施要點、技術細節和驗收標準"),
      implementationGuide: z
        .string()
        .describe(
          "此特定任務的具體實現方法和步驟，請參考之前的分析結果提供精簡pseudocode"
        ),
      dependencies: z
        .array(z.string())
        .optional()
        .describe(
          "此任務依賴的前置任務ID或任務名稱列表，支持兩種引用方式，名稱引用更直觀，是一個字串陣列"
        ),
      notes: z
        .string()
        .optional()
        .describe("補充說明、特殊處理要求或實施建議（選填）"),
      relatedFiles: z
        .array(
          z.object({
            path: z
              .string()
              .min(1, {
                message: "文件路徑不能為空",
              })
              .describe("文件路徑，可以是相對於項目根目錄的路徑或絕對路徑"),
            type: z
              .nativeEnum(RelatedFileType)
              .describe(
                "文件類型 (TO_MODIFY: 待修改, REFERENCE: 參考資料, CREATE: 待建立, DEPENDENCY: 依賴文件, OTHER: 其他)"
              ),
            description: z
              .string()
              .min(1, {
                message: "文件描述不能為空",
              })
              .describe("文件描述，用於說明文件的用途和內容"),
            lineStart: z
              .number()
              .int()
              .positive()
              .optional()
              .describe("相關代碼區塊的起始行（選填）"),
            lineEnd: z
              .number()
              .int()
              .positive()
              .optional()
              .describe("相關代碼區塊的結束行（選填）"),
          })
        )
        .optional()
        .describe(
          "與任務相關的文件列表，用於記錄與任務相關的代碼文件、參考資料、要建立的文件等（選填）"
        ),
      verificationCriteria: z
        .string()
        .optional()
        .describe("此特定任務的驗證標準和檢驗方法"),
    })
  )
  .min(1, {
    message: "請至少提供一個任務",
  })
  .describe("結構化的任務清單");
```

### Related File Type Enum

```typescript
enum RelatedFileType {
  TO_MODIFY = "TO_MODIFY",     // 待修改
  REFERENCE = "REFERENCE",     // 參考資料
  CREATE = "CREATE",           // 待建立
  DEPENDENCY = "DEPENDENCY",   // 依賴文件
  OTHER = "OTHER"              // 其他
}
```

### Task Management Schemas

#### `deleteTaskSchema`
```typescript
export const deleteTaskSchema = z.object({
  taskId: z
    .string()
    .regex(UUID_V4_REGEX, {
      message: "任務ID格式無效，請提供有效的UUID v4格式",
    })
    .describe("待刪除任務的唯一標識符，必須是系統中存在且未完成的任務ID"),
});
```

#### `updateTaskContentSchema`
```typescript
export const updateTaskContentSchema = z.object({
  taskId: z
    .string()
    .regex(UUID_V4_REGEX, {
      message: "任務ID格式無效，請提供有效的UUID v4格式",
    })
    .describe("待更新任務的唯一標識符，必須是系統中存在且未完成的任務ID"),
  name: z.string().optional().describe("任務的新名稱（選填）"),
  description: z.string().optional().describe("任務的新描述內容（選填）"),
  notes: z.string().optional().describe("任務的新補充說明（選填）"),
  dependencies: z
    .array(z.string())
    .optional()
    .describe("任務的新依賴關係（選填）"),
  relatedFiles: z
    .array(
      z.object({
        path: z
          .string()
          .min(1, { message: "文件路徑不能為空，請提供有效的文件路徑" })
          .describe("文件路徑，可以是相對於項目根目錄的路徑或絕對路徑"),
        type: z
          .nativeEnum(RelatedFileType)
          .describe(
            "文件與任務的關係類型 (TO_MODIFY, REFERENCE, CREATE, DEPENDENCY, OTHER)"
          ),
        description: z.string().optional().describe("文件的補充描述（選填）"),
        lineStart: z
          .number()
          .int()
          .positive()
          .optional()
          .describe("相關代碼區塊的起始行（選填）"),
        lineEnd: z
          .number()
          .int()
          .positive()
          .optional()
          .describe("相關代碼區塊的結束行（選填）"),
      })
    )
    .optional()
    .describe(
      "與任務相關的文件列表，用於記錄與任務相關的代碼文件、參考資料、要建立的檔案等（選填）"
    ),
  implementationGuide: z
    .string()
    .optional()
    .describe("任務的新實現指南（選填）"),
  verificationCriteria: z
    .string()
    .optional()
    .describe("任務的新驗證標準（選填）"),
});
```

### Thought Processing Schema: `processThoughtSchema`

```typescript
export const processThoughtSchema = z.object({
  thought: z.string().describe("思維內容"),
  thought_number: z.number().positive().describe("當前思維步驟序號"),
  total_thoughts: z.number().positive().describe("預計總思維步驟數"),
  next_thought_needed: z.boolean().describe("是否需要下一個思維步驟"),
  stage: z.string().describe("思維階段，如 Problem Definition、Information Gathering、Research、Analysis、Synthesis、Conclusion、Critical Questioning、Planning"),
  tags: z.array(z.string()).optional().describe("思維標籤"),
  axioms_used: z.array(z.string()).optional().describe("使用的公理列表"),
  assumptions_challenged: z.array(z.string()).optional().describe("質疑的假設列表"),
});
```

## Schema Characteristics and Design Patterns

### Validation Rules
- **Task Name**: Maximum 100 characters
- **Task Description**: Minimum 10 characters
- **Task ID**: Must be valid UUID v4 format
- **File Paths**: Must not be empty
- **Line Numbers**: Must be positive integers

### Granularity Controls
- **Minimum Viable Task**: 1-2 working days (8-16 hours)
- **Maximum Complexity**: Single technical domain
- **Recommended Task Count**: ≤ 10 subtasks at once
- **Task Raw Length**: ≤ 5,000 characters
- **Depth Limitation**: ≤ 3 levels (Modules > Processes > Steps)

### Internationalization
- Schemas include Chinese descriptions and error messages
- Multi-language template system support
- Configurable prompt system via environment variables

## Missing Schemas (Referenced but not detailed)

The following schemas are registered in `src/index.ts` but their detailed definitions were not available in the analysis:

- `planTaskSchema` - Task planning parameters
- `analyzeTaskSchema` - Task analysis parameters  
- `reflectTaskSchema` - Task reflection parameters
- `executeTaskSchema` - Task execution parameters
- `verifyTaskSchema` - Task verification parameters
- `listTasksSchema` - Task listing parameters
- `queryTaskSchema` - Task query parameters
- `getTaskDetailSchema` - Task detail retrieval parameters
- `clearAllTasksSchema` - Clear all tasks parameters
- `initProjectRulesSchema` - Project rules initialization parameters
- `researchModeSchema` - Research mode parameters

## Key Implementation Notes

1. **UUID v4 Validation**: Uses regex pattern for UUID validation
2. **Enum Usage**: RelatedFileType enum for type safety
3. **Optional Fields**: Many fields are optional to provide flexibility
4. **Array Validation**: Dependencies and related files use array schemas
5. **String Length Validation**: Both minimum and maximum constraints
6. **Nested Object Validation**: Complex nested structures for related files
7. **Descriptive Messages**: Rich descriptions for AI agent understanding

This schema system enables sophisticated task management with proper validation, dependency tracking, and file association capabilities that far exceed simple task management systems.