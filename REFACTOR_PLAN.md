# Code Polish & Refactoring Plan

**Branch:** `refactor/code-polish-and-cleanup`
**Date:** 2025-11-29
**Goal:** Improve code quality, eliminate duplication, and add polish without changing functionality

## Overview

This refactoring addresses technical debt accumulated during feature development:
- **Code duplication** across pages (3 large functions duplicated)
- **Magic strings** throughout codebase
- **Missing cleanup logic** for generated recipes
- **Inconsistent patterns** in error handling and path construction

## Guiding Principles

✅ **Keep it simple** - No over-engineering
✅ **No breaking changes** - All functionality stays the same
✅ **Progressive** - Small, testable changes
✅ **DRY** - Don't Repeat Yourself

---

## Phase 1: High Priority (Code Duplication)

### Task 1.1: Create Shared Recipe Feedback Module
**File:** `lib/recipe_feedback.py` (NEW)

Extract 3 duplicated functions from `cooking_mode.py` and `generate_recipes.py`:
- `save_recipe_feedback()` - 172 lines
- `is_staple_ingredient()` - 37 lines
- `update_pantry_after_cooking()` - 88 lines

**Impact:** Eliminates ~300 lines of duplicated code

### Task 1.2: Update Page Imports
Update both pages to import from shared module:
- `pages/cooking_mode.py`
- `pages/generate_recipes.py`

**Test:** Verify cooking flow works end-to-end

---

## Phase 2: Medium Priority (Architecture)

### Task 2.1: Create Constants Module
**File:** `lib/constants.py` (NEW)

Define constants for:
- Recipe sources: `GENERATED`, `LOVED`, `LIKED`, `NOT_AGAIN`
- Rating thresholds: `RATING_LOVED_THRESHOLD = 5`, `RATING_LIKED_THRESHOLD = 3`

### Task 2.2: Replace Magic Strings
Update files to use constants:
- `lib/weekly_plan_manager.py`
- `lib/recipe_feedback.py` (after Phase 1)
- `pages/weekly_planner.py`
- `pages/generate_recipes.py`

### Task 2.3: Add Generated Recipe Cleanup
**File:** `lib/weekly_plan_manager.py`

Add function: `remove_generated_recipe(recipe_name: str)`

Call from:
- `remove_meal_from_plan()` when source is Generated
- `save_recipe_feedback()` in recipe_feedback module

### Task 2.4: Improve Path Construction
**File:** `lib/active_recipe_manager.py`

Extract helper: `_get_active_recipe_path()` to centralize path logic

---

## Phase 3: Low Priority (Polish)

### Task 3.1: Improve Exception Handling
Replace bare `except:` with specific `except AttributeError:` for cache clearing

### Task 3.2: Better Duplicate Detection
In `save_generated_recipe()`, use regex-based parsing instead of string matching

### Task 3.3: Add Session Cleanup Helper
**File:** `lib/session_helpers.py` (NEW)

Create `clear_cooking_session()` helper and use in both pages

---

## Testing Checklist

After each phase, verify:
- [ ] Generate new recipes → works
- [ ] Add recipe to plan → works
- [ ] Cook from weekly planner → works
- [ ] Rate recipe after cooking → works
- [ ] Pantry updates correctly → works
- [ ] Session persistence across refresh → works

---

## Success Metrics

- **Lines removed:** ~300+ (from deduplication)
- **New modules:** 3 (`recipe_feedback.py`, `constants.py`, `session_helpers.py`)
- **Magic strings replaced:** ~20+
- **Bugs fixed:** 2-3 edge cases
- **Functionality changed:** 0 (all existing features work identically)

---

## Implementation Order

1. ✅ Phase 1 (deduplication) - Biggest impact
2. ✅ Phase 2.1 & 2.2 (constants) - Foundation for other changes
3. ✅ Phase 2.3 & 2.4 (cleanup & paths) - Architecture improvements
4. ✅ Phase 3 (polish) - Nice-to-haves

Each task is independent and can be committed separately for easy rollback if needed.
