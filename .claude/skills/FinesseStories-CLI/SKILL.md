```markdown
# FinesseStories-CLI Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches you the core development patterns and conventions used in the FinesseStories-CLI TypeScript codebase. You'll learn how to structure files, write imports/exports, and follow the project's unique coding style. While no specific workflows were detected, this guide provides best practices and command suggestions to streamline your development process.

## Coding Conventions

### File Naming
- Use **PascalCase** for all file names.
  - **Example:** `StoryManager.ts`, `UserInputHandler.ts`

### Import Style
- Use **relative imports** for referencing other modules within the project.
  - **Example:**
    ```typescript
    import { StoryManager } from './StoryManager';
    ```

### Export Style
- Use **named exports** for all exported functions, classes, or constants.
  - **Example:**
    ```typescript
    export function runCLI() { ... }
    export class StoryManager { ... }
    ```

### Commit Patterns
- Commit messages are freeform, sometimes with prefixes, and average 52 characters in length.
  - **Example:**  
    ```
    Add support for multiple story formats
    Fix bug in input parser
    ```

## Workflows

_No specific workflows were detected in the repository. Below are general development steps you can follow:_

### Creating a New Module
**Trigger:** When you need to add new functionality.
**Command:** `/create-module`

1. Create a new file in PascalCase (e.g., `NewFeature.ts`).
2. Use named exports for your functions or classes.
3. Import dependencies using relative paths.
4. Write corresponding test files named `NewFeature.test.ts`.

### Running Tests
**Trigger:** When you want to verify your code.
**Command:** `/run-tests`

1. Locate test files matching the pattern `*.test.*`.
2. Use your preferred test runner (framework not specified).
3. Review test results and address any failures.

## Testing Patterns

- **Test File Naming:**  
  Test files follow the pattern `*.test.*` (e.g., `StoryManager.test.ts`).
- **Testing Framework:**  
  The specific framework is unknown; use the project's existing setup or introduce one as needed.
- **Example Test File:**
  ```typescript
  import { runCLI } from './CLI';

  test('runCLI executes without errors', () => {
    expect(() => runCLI()).not.toThrow();
  });
  ```

## Commands
| Command         | Purpose                                      |
|-----------------|----------------------------------------------|
| /create-module  | Scaffold a new module with proper conventions|
| /run-tests      | Run all test files in the project            |
```