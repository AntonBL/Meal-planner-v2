# Plant Tracker Learnings

**Knowledge transfer from Meal Planner v2 to Plant Health Tracker app**

---

## Overview

This folder contains comprehensive learnings, patterns, and best practices extracted from the Meal Planner v2 project. These documents will help you build a professional, maintainable Plant Health Tracker app using **SwiftUI (iOS)** and **FastAPI (Python backend)**.

---

## 📚 Documentation Index

### 1. [Architecture Principles](./01-architecture-principles.md)
**Start here!** Comprehensive overview of system architecture and design principles.

**Topics covered:**
- Overall system architecture (SwiftUI + FastAPI)
- SOLID principles with examples
- DRY, YAGNI, KISS patterns
- Layer separation (API → Service → Repository)
- Repository and Service patterns
- Dependency injection
- Recommended file structure
- Key learnings from Meal Planner v2

**When to read:** Before starting development, to understand the big picture.

---

### 2. [Programming Patterns](./02-programming-patterns.md)
Practical code patterns and best practices for Python and general development.

**Topics covered:**
- Type hints and type safety
- Structured logging patterns
- Error handling with custom exceptions
- Testing patterns (AAA, fixtures, parametrized tests)
- Data access patterns (Repository, JSON storage)
- API integration patterns (LLM providers, retry logic)
- Code quality checklist

**When to read:** While writing code, as a reference for specific patterns.

---

### 3. [FastAPI Backend Guide](./03-fastapi-backend-guide.md)
Complete guide to building the Python FastAPI backend.

**Topics covered:**
- Project setup and structure
- FastAPI application configuration
- API route patterns (CRUD operations)
- Dependency injection in FastAPI
- Pydantic models for request/response
- JWT authentication
- Error handling and global exception handlers
- Testing FastAPI endpoints
- Deployment considerations

**When to read:** When implementing the backend API.

---

### 4. [SwiftUI Frontend Guide](./04-swiftui-frontend-guide.md)
Complete guide to building the iOS app with SwiftUI.

**Topics covered:**
- Xcode project setup
- MVVM architecture for SwiftUI
- Data models with SwiftData
- Networking layer (API client)
- Local storage with SwiftData
- Camera and photo library integration
- Local and push notifications
- Keychain for secure token storage
- Key SwiftUI patterns

**When to read:** When implementing the iOS frontend.

---

### 5. [Claude Collaboration Guide](./05-claude-collaboration.md)
How to work effectively with Claude Code (AI assistant).

**Topics covered:**
- Setting up `claude.md` for your project
- How to communicate effectively with Claude
- Best practices for requesting features
- Common collaboration patterns
- What Claude excels at
- What to review carefully
- Example workflows

**When to read:** Before working with Claude Code, to maximize productivity.

---

### 6. [Quick Reference](./06-quick-reference.md)
Fast-access cheatsheet for common commands and patterns.

**Topics covered:**
- Architecture quick reference
- Python and FastAPI commands
- Testing commands
- Code patterns cheatsheet
- Decision guide (where to put code, when to build features)
- Common gotchas
- Daily workflow checklist

**When to read:** While developing, as a quick lookup reference.

---

### 7. [LLM Integration Guide](./07-llm-integration-guide.md)
**NEW!** Complete guide to integrating Claude and Gemini APIs for plant health analysis.

**Topics covered:**
- Environment setup (API keys, SDK installation)
- Provider protocol pattern (swap LLMs easily)
- Text generation with Claude & Gemini
- **Vision API integration** (plant health analysis from photos)
- Error handling and retry logic
- Cost optimization strategies
- Testing with mock providers
- Real-world examples (complete plant health service)

**When to read:** Before implementing plant health analysis features. **Essential for vision-based features!**

---

### 8. [Template: claude.md](./template-claude.md)
Ready-to-use `claude.md` template for your Plant Tracker project.

**What it is:** A complete instruction manual for Claude Code to follow when working on your project. Copy this to your new project as `claude.md`.

**When to use:** At the start of your project, before working with Claude Code.

---

## 🚀 Getting Started

### Step 1: Understand the Architecture
Read `01-architecture-principles.md` to understand:
- Why SwiftUI + FastAPI?
- How the layers work together
- What goes where (iOS vs backend)
- Design patterns you'll use

### Step 2: Set Up Your Project
Follow the setup instructions in:
- `03-fastapi-backend-guide.md` for backend
- `04-swiftui-frontend-guide.md` for iOS app

### Step 3: Copy the Claude Template
Copy `template-claude.md` to your new project as `claude.md` and customize it for your needs.

### Step 4: Start Building
Use the guides as references while building:
- Keep `02-programming-patterns.md` open for code patterns
- Reference `06-quick-reference.md` for commands
- Follow `05-claude-collaboration.md` for working with Claude

---

## 🎯 Recommended Development Approach

### Phase 1: Offline-First MVP (Week 1-2)
**Goal:** Working iOS app with local storage

**Build:**
- ✅ SwiftUI app with basic UI
- ✅ Local storage with SwiftData
- ✅ CRUD operations (create, read, update, delete plants)
- ✅ Watering tracking (local only)
- ✅ Local notifications for watering reminders
- ✅ Camera/photo library integration

**You'll have:** A fully functional app you can use yourself!

### Phase 2: Add Backend (Week 3-4)
**Goal:** FastAPI backend with API sync

**Build:**
- ✅ FastAPI backend with endpoints
- ✅ Database (SQLite to start)
- ✅ API client in iOS app
- ✅ Background sync (local → server)
- ✅ Image upload and storage

**You'll have:** Multi-device sync capability!

### Phase 3: Advanced Features (Week 5+)
**Goal:** Image analysis and advanced features

**Build:**
- ✅ Plant health analysis (Claude Vision API)
- ✅ Push notifications (if needed)
- ✅ Sharing plants with friends
- ✅ Advanced analytics

**You'll have:** A polished, feature-rich app!

---

## 💡 Key Insights from Meal Planner v2

### ✅ What Worked Well

1. **Starting Simple**
   - Began with file-based storage before databases
   - Used Streamlit (simple) instead of React (complex)
   - Added features incrementally

2. **Strong Architecture**
   - Repository pattern made storage swappable
   - Service layer kept business logic organized
   - Dependency injection made testing easy

3. **Type Safety**
   - Type hints caught bugs early
   - Made refactoring safer
   - Improved IDE autocomplete

4. **Comprehensive Logging**
   - Structured logging helped debug production issues
   - Context in logs made troubleshooting faster

5. **Testing**
   - Tests provided confidence during refactoring
   - Mocked dependencies kept tests fast
   - AAA pattern made tests readable

### ⚠️ Lessons Learned

1. **Don't Over-Engineer Early**
   - Started with complex abstractions that weren't needed
   - YAGNI principle is real – build what you need NOW

2. **Logging is Critical**
   - Wished we had more logging from day 1
   - Structured logging (with context) >> simple messages

3. **Document as You Go**
   - Architecture decisions are hard to remember later
   - Claude.md file is invaluable for consistency

4. **Fail Fast with Validation**
   - Early input validation prevents debugging later
   - Type hints + Pydantic catch issues at the boundary

5. **Test Outcomes, Not Implementation**
   - Implementation-focused tests break during refactoring
   - Outcome-focused tests remain stable

---

## 🔧 Tools & Technologies

### Backend (Python)
- **FastAPI** - Modern, fast web framework
- **Pydantic** - Data validation
- **pytest** - Testing framework
- **ruff** - Fast linter
- **mypy** - Type checker
- **uv** - Fast package installer

### Frontend (iOS)
- **SwiftUI** - Declarative UI framework
- **SwiftData** - Local database
- **Combine** - Reactive programming
- **PhotosUI** - Photo picker
- **UserNotifications** - Notifications

### APIs
- **Anthropic Claude** - LLM and vision analysis
- **APNs** - Push notifications (if needed)

---

## 📖 Additional Resources

### Architecture & Patterns
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SwiftUI Tutorials](https://developer.apple.com/tutorials/swiftui)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [MVVM in SwiftUI](https://developer.apple.com/documentation/swiftui/model-data)

### Learning
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Pydantic Models](https://docs.pydantic.dev/)
- [SwiftData](https://developer.apple.com/documentation/swiftdata)
- [pytest Documentation](https://docs.pytest.org/)

---

## 🤝 How to Use These Docs

**For Quick Lookups:**
→ Use `06-quick-reference.md`

**For Understanding Concepts:**
→ Read `01-architecture-principles.md`

**For Implementation Details:**
→ Reference `03-fastapi-backend-guide.md` or `04-swiftui-frontend-guide.md`

**For Working with Claude:**
→ Follow `05-claude-collaboration.md`

**For Code Patterns:**
→ Check `02-programming-patterns.md`

---

## 📝 Your Initial Thoughts (From Request)

You wanted to build a plant health tracker with:

**Architecture:**
- SwiftUI iOS app
- Python FastAPI backend
- Real iOS features (camera, notifications, widgets)
- Business logic in Python (where you're fast)

**Notifications:**
- Start with local notifications (easy, offline)
- Add push later if needed (server-triggered)

**Camera:**
- Use PhotosUI for simple photo capture
- AVFoundation if you need full control

**Development Approach:**
- Phase 1: Real app shell (offline-first)
- Phase 2: Python superpowers (API backend)
- Phase 3: Share with friends (auth, push notifications)

**✅ This approach is solid!** These documents will help you execute on this plan.

---

## 🎉 Ready to Build!

You now have:
- ✅ Comprehensive architecture guides
- ✅ Detailed implementation patterns
- ✅ FastAPI backend guide
- ✅ SwiftUI frontend guide
- ✅ Claude collaboration strategies
- ✅ Quick reference for common tasks

**Next steps:**
1. Create your new Plant Tracker project
2. Copy `template-claude.md` to your project as `claude.md`
3. Start with Phase 1 (offline-first MVP)
4. Reference these docs as you build
5. Iterate and improve!

**Good luck building your Plant Tracker app! 🌱**

---

## 📞 Questions?

If you have questions about any of these patterns or need clarification:
1. Check the relevant guide in this folder
2. Look at the Meal Planner v2 codebase for examples
3. Ask Claude Code with specific questions (using `05-claude-collaboration.md` patterns)

**Remember:** Start simple, iterate, and build incrementally. You've got this! 🚀
