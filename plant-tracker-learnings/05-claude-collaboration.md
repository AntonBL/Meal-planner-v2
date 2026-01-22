# Working with Claude Code - Collaboration Guide

**How to Work Effectively with Claude Code (AI Assistant)**

---

## Table of Contents

1. [What is Claude Code?](#what-is-claude-code)
2. [Setting Up claude.md](#setting-up-claudemd)
3. [How to Communicate Effectively](#how-to-communicate-effectively)
4. [Best Practices](#best-practices)
5. [Common Patterns](#common-patterns)
6. [What Claude Code Excels At](#what-claude-code-excels-at)
7. [What to Review Carefully](#what-to-review-carefully)

---

## What is Claude Code?

Claude Code is an AI coding assistant that can:
- Write, refactor, and debug code
- Create tests
- Explain code and architecture
- Search codebases
- Follow project-specific guidelines
- Run commands and manage your development workflow

**Key principle:** Claude Code works best when you provide clear context and guidelines.

---

## Setting Up claude.md

The `claude.md` file is Claude Code's instruction manual for your project. It ensures consistency and quality.

### Template claude.md for Plant Tracker

```markdown
# Claude AI Assistant Instructions

**Instructions for Claude when working on the Plant Tracker project**

---

## Overview

You are working on a professional Python FastAPI backend and SwiftUI iOS frontend for plant health tracking. Follow professional software engineering practices at all times.

---

## Required Reading

**BEFORE writing any code, you MUST:**

1. Read the architecture principles in `docs/architecture-principles.md`
2. Review the programming patterns in `docs/programming-patterns.md`
3. Check existing code to maintain consistency

---

## Core Principles

### Code Quality Standards

✅ **ALWAYS:**
- Use structured logging (never `print()` statements in Python)
- Include complete type hints on all Python functions
- Write docstrings (Google style) for all public functions/classes
- Follow DRY, YAGNI, KISS, and SOLID principles
- Handle errors with specific exception classes
- Write tests with pytest (Python) or XCTest (Swift)
- Use `pathlib.Path` instead of string paths (Python)
- Validate inputs early (fail fast)

❌ **NEVER:**
- Use `print()` for output (use `logging` module)
- Commit code without type hints (Python)
- Leave functions without docstrings
- Repeat code (extract into functions)
- Over-engineer solutions (YAGNI)
- Ignore errors or use bare `except:` clauses
- Use `os.path` when `pathlib` is clearer

### Testing Requirements

Every new feature MUST include:
- Unit tests using pytest (Python) or XCTest (Swift)
- Tests for happy path AND error cases
- Mocked external dependencies (API calls, file I/O)
- Isolated tests that don't depend on each other
- AAA pattern (Arrange, Act, Assert)

---

## Development Workflow

### 1. Before Writing Code

- [ ] Understand the requirement completely
- [ ] Check if similar code already exists (DRY)
- [ ] Consider if this feature is actually needed (YAGNI)
- [ ] Plan the simplest solution (KISS)

### 2. While Writing Code

- [ ] Use type hints everywhere (Python)
- [ ] Add logging with structured context (Python)
- [ ] Write docstrings as you go
- [ ] Keep functions small and focused (SRP)
- [ ] Handle errors explicitly

### 3. After Writing Code

- [ ] Write tests (aim for 80%+ coverage)
- [ ] Run linter: `ruff check --fix .` (Python)
- [ ] Run type checker: `mypy .` (Python)
- [ ] Run tests: `pytest --cov` (Python)

---

## Communication with User

When presenting code changes:

1. **Explain the reasoning**: Why you chose this approach
2. **Reference principles**: Mention which principles you applied
3. **Highlight testing**: Show what tests you wrote
4. **Note trade-offs**: If you made any compromises, explain them

---

## File Organization

### Python Backend
```
app/
├── api/           # API routes
├── services/      # Business logic
├── repositories/  # Data access
├── models/        # Data models
└── utils/         # Utilities
```

### SwiftUI Frontend
```
PlantTracker/
├── Models/        # Data models
├── Views/         # UI
├── ViewModels/    # MVVM view models
└── Services/      # Networking, etc.
```

---

## Remember

You are building **production-quality software**. Every line of code should reflect professional software engineering practices.

**Quality over speed. Simplicity over cleverness. Tests over hope.**
```

---

## How to Communicate Effectively

### ✅ Good Requests

**Be specific:**
```
❌ "Make the app better"
✅ "Add a feature to track plant health using image analysis with Claude Vision API.
    The feature should:
    1. Allow users to upload a photo
    2. Send it to Claude API for analysis
    3. Display the health status (healthy, needs attention, critical)
    4. Store the analysis in the database"
```

**Provide context:**
```
✅ "I'm getting a 404 error when trying to fetch a plant by ID. The endpoint is
    /api/plants/{plant_id} and I'm passing a valid UUID. Here's the error message: [paste error].
    The code is in app/api/plants.py, lines 45-60."
```

**Reference existing patterns:**
```
✅ "Add a new endpoint for watering history, following the same pattern as the
    plants.py endpoints. It should return a list of watering events for a specific plant."
```

### ❌ Avoid Vague Requests

```
❌ "Fix the bug"
   → Which bug? Where? What's the error?

❌ "Add tests"
   → For what feature? What scenarios?

❌ "Make it work"
   → What's not working? What should it do?
```

---

## Best Practices

### 1. Start with Architecture

**Before building features, establish architecture:**
```
"Let's plan the architecture for the plant tracker app.
I want to use:
- FastAPI for the backend
- SwiftUI for iOS frontend
- Offline-first approach with local storage
- API sync in the background

Can you create a document outlining:
1. Overall system architecture
2. Data flow (offline → sync → server)
3. Recommended file structure
4. Key design patterns to use"
```

### 2. Iterate Incrementally

**Build features step-by-step:**
```
Phase 1: "Create the basic Plant model with SwiftData for local storage"
Phase 2: "Add CRUD operations for plants (create, read, update, delete)"
Phase 3: "Add FastAPI backend endpoints"
Phase 4: "Implement sync between local storage and API"
```

### 3. Request Tests Explicitly

**Always ask for tests:**
```
"Add a watering reminder feature. Make sure to include:
1. Unit tests for the watering logic
2. Tests for edge cases (past dates, invalid plant IDs)
3. Mock the notification service in tests"
```

### 4. Ask for Explanations

**Request learning insights:**
```
"Can you explain why we're using the Repository pattern for data access
instead of calling the API directly from ViewModels?"
```

### 5. Review Code Together

**Request code reviews:**
```
"I wrote this PlantService class. Can you review it for:
1. Adherence to SOLID principles
2. Proper error handling
3. Testability
4. Any potential bugs or edge cases I missed?"
```

---

## Common Patterns

### Pattern 1: Feature Implementation

```
You: "I need to add a feature for recording when I water a plant.
      Requirements:
      - Update the plant's last_watered timestamp
      - Calculate the next watering date
      - Schedule a local notification
      - Sync with the API backend

      Please:
      1. Create the backend endpoint (FastAPI)
      2. Add the iOS service method
      3. Update the ViewModel
      4. Write tests for both
      5. Follow the existing code patterns"

Claude: [Implements feature with tests, following project guidelines]
```

### Pattern 2: Debugging

```
You: "I'm getting this error when trying to decode the API response:
      [paste error + relevant code]

      The endpoint is /api/plants and the response looks like:
      [paste response JSON]

      What's wrong?"

Claude: [Analyzes error, identifies issue, provides fix]
```

### Pattern 3: Refactoring

```
You: "This PlantListViewModel is getting too large (200+ lines).
      Can you help refactor it to follow SRP?
      Current code: [paste code or file reference]"

Claude: [Suggests splitting into smaller, focused classes]
```

### Pattern 4: Learning

```
You: "Can you explain how the offline-first sync pattern works in our app?
      Specifically:
      1. How do we handle conflicts?
      2. When do we sync with the server?
      3. What happens if the API call fails?"

Claude: [Provides detailed explanation with examples from your code]
```

---

## What Claude Code Excels At

### ✅ Strengths

1. **Writing boilerplate code**
   - API routes, models, repositories
   - Test scaffolding
   - Configuration files

2. **Following established patterns**
   - Replicating existing code structure
   - Maintaining consistency
   - Applying your project's conventions

3. **Generating tests**
   - Unit tests
   - Integration tests
   - Test fixtures and mocks

4. **Refactoring**
   - Breaking up large functions
   - Applying design patterns
   - Improving code organization

5. **Documentation**
   - Docstrings
   - README files
   - Architecture documents

6. **Debugging**
   - Analyzing error messages
   - Identifying logic errors
   - Suggesting fixes

7. **Searching codebases**
   - Finding files/functions
   - Understanding code flow
   - Tracing dependencies

---

## What to Review Carefully

### ⚠️ Areas Requiring Human Review

1. **Business Logic**
   - Verify calculations (watering schedules, etc.)
   - Check edge cases
   - Validate assumptions

2. **Security**
   - Authentication/authorization logic
   - API key handling
   - Data validation

3. **API Integrations**
   - Error handling for external APIs
   - Retry logic
   - Rate limiting

4. **Performance**
   - Database query efficiency
   - Memory usage
   - Network request optimization

5. **User Experience**
   - UI/UX decisions
   - Error messages
   - Loading states

6. **Data Migration**
   - Database schema changes
   - Data transformation logic
   - Backwards compatibility

### Review Checklist

After Claude writes code:

- [ ] Does it solve the actual problem?
- [ ] Are there any edge cases not handled?
- [ ] Is error handling appropriate?
- [ ] Are tests comprehensive?
- [ ] Does it follow project conventions?
- [ ] Is it secure (no exposed secrets, proper validation)?
- [ ] Is performance acceptable?
- [ ] Is the code maintainable?

---

## Tips for Effective Collaboration

### 1. Provide Examples

**Show, don't just tell:**
```
"Add a health analysis endpoint, similar to this watering endpoint:
[paste example endpoint code]

The health endpoint should:
- Accept an image upload
- Return a health status
- Follow the same error handling pattern"
```

### 2. Reference Documentation

**Point to existing docs:**
```
"Follow the FastAPI patterns described in docs/03-fastapi-backend-guide.md,
specifically the file upload section."
```

### 3. Iterate and Refine

**Start broad, then refine:**
```
You: "Create a plant model with basic fields"
Claude: [Creates model]
You: "Add computed properties for needsWatering and nextWateringDate"
Claude: [Adds properties]
You: "Add validation to ensure wateringFrequencyDays is between 1 and 365"
Claude: [Adds validation]
```

### 4. Ask for Options

**Get alternatives:**
```
"I need to sync plant data between the iOS app and backend.
What are 3 different approaches I could take, with pros/cons of each?"
```

### 5. Request Explanations

**Learn as you build:**
```
"Before implementing, can you explain:
1. Why we need dependency injection here?
2. How the Repository pattern helps with testing?
3. What the trade-offs are?"
```

---

## Example Workflow

### Building a New Feature: Plant Health Analysis

**Step 1: Planning**
```
You: "I want to add plant health analysis using photos. Before implementing,
      let's plan:
      1. What endpoints do we need?
      2. How should the data flow work?
      3. What models/classes are needed?
      4. How do we integrate with Claude Vision API?"

Claude: [Provides architectural plan]
```

**Step 2: Backend Implementation**
```
You: "Let's start with the backend. Create:
      1. A HealthReport model
      2. A POST /api/health/analyze endpoint that accepts an image
      3. A HealthAnalysisService that calls Claude Vision API
      4. Tests for the service

      Follow the patterns in our existing code."

Claude: [Implements backend with tests]
```

**Step 3: Frontend Implementation**
```
You: "Now the iOS side. Create:
      1. A HealthReport Swift model
      2. A HealthService for API calls
      3. An ImagePicker for photo selection
      4. A HealthAnalysisView with upload button

      Use MVVM pattern like our other views."

Claude: [Implements frontend]
```

**Step 4: Integration**
```
You: "Connect everything:
      1. Wire up the ImagePicker to the ViewModel
      2. Call the API when image is selected
      3. Display the results
      4. Handle errors gracefully"

Claude: [Implements integration]
```

**Step 5: Review and Refine**
```
You: "Let's review the implementation:
      1. Are we handling all error cases?
      2. What about rate limiting for the API?
      3. Should we cache results?
      4. Any edge cases we're missing?"

Claude: [Reviews and suggests improvements]
```

---

## Summary

**Effective collaboration with Claude Code:**

1. **Set up claude.md** with your project's guidelines
2. **Be specific** in your requests
3. **Provide context** (error messages, relevant code, requirements)
4. **Reference existing patterns** to maintain consistency
5. **Iterate incrementally** (build features step-by-step)
6. **Request tests** for all new code
7. **Review carefully** (business logic, security, performance)
8. **Ask questions** to learn as you build

**Remember:** Claude Code is a powerful tool, but you're the architect. Use it to accelerate development while maintaining high code quality and understanding the system you're building.

---

## Next Steps

1. Create your `claude.md` file based on the template
2. Review `06-quick-reference.md` for command shortcuts
3. Start building your Plant Tracker app!
