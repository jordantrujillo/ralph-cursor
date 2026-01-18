# PRD Generator

Create detailed Product Requirements Documents that are clear, actionable, and suitable for implementation.

---

## The Job

1. Receive a feature description from the user
2. Ask 3-5 essential clarifying questions (with lettered options)
3. **Assess scope** - determine if phases are needed (6+ stories, 10+ files, spans multiple areas)
4. Generate a structured PRD based on answers
5. **Always create phases for large features** - break down into logical, reviewable phases
6. Save to `tasks/prd-[feature-name].md`

**Important:** Do NOT start implementing. Just create the PRD.

**Phase Strategy:** If the feature will touch many files, have many stories, or span multiple codebase areas, automatically organize it into phases. This enables incremental PRs and better code review.

---

## Step 1: Clarifying Questions

Ask only critical questions where the initial prompt is ambiguous. Focus on:

- **Problem/Goal:** What problem does this solve?
- **Core Functionality:** What are the key actions?
- **Scope/Boundaries:** What should it NOT do?
- **Success Criteria:** How do we know it's done?

**While asking questions, also assess scope:**
- How many files will this likely touch? (database, API, UI, etc.)
- How many distinct areas of the codebase?
- Does this span backend and frontend?
- Based on this, determine if phases will be needed (see Phase Guidelines below)

### Format Questions Like This:

```
1. What is the primary goal of this feature?
   A. Improve user onboarding experience
   B. Increase user retention
   C. Reduce support burden
   D. Other: [please specify]

2. Who is the target user?
   A. New users only
   B. Existing users only
   C. All users
   D. Admin users only

3. What is the scope?
   A. Minimal viable version
   B. Full-featured implementation
   C. Just the backend/API
   D. Just the UI
```

This lets users respond with "1A, 2C, 3B" for quick iteration.

---

## Step 2: PRD Structure

Generate the PRD with these sections:

### 1. Introduction/Overview
Brief description of the feature and the problem it solves.

### 2. Goals
Specific, measurable objectives (bullet list).

### 3. Phases (Required for Large Features)
**Always break down large features into phases.** Each phase will be implemented on its own branch, allowing for incremental review and smaller PRs.

**When to create phases:**
- **Always create phases if:** The feature will touch many files (10+ files), has many user stories (6+ stories), or spans multiple areas of the codebase
- **Create phases if:** The feature involves database changes + API changes + UI changes (these are natural phase boundaries)
- **Create phases if:** The feature has clear logical groupings (e.g., "backend setup" → "API endpoints" → "UI components")
- **You can skip phases only if:** The feature is very small (3-4 stories, 2-3 files) and tightly focused

**Format:**
```markdown
## Phases

### Phase 1: [Phase Name]
**Description:** Brief description of what this phase accomplishes.
**Branch:** `ralph/[feature-name]-phase-1` (branched from current branch)

**User Stories:**
- US-001: [Story title]
- US-002: [Story title]
...
- US-007: Code Review - Edge Case Analysis
- US-008: Security Review - Production Hardening
- US-009: Test Review - Quality Assurance

### Phase 2: [Phase Name]
**Description:** Brief description of what this phase accomplishes.
**Branch:** `ralph/[feature-name]-phase-2` (built on top of phase-1 branch)

**User Stories:**
- US-005: [Story title]
- US-006: [Story title]
...
- US-010: Code Review - Edge Case Analysis
- US-011: Security Review - Production Hardening
- US-012: Test Review - Quality Assurance
```

**Phase Guidelines:**
- Each phase should be a logical, reviewable unit of work (typically 3-6 stories)
- Phases should build on each other (later phases depend on earlier ones)
- Each phase gets its own branch: `ralph/[feature-name]-phase-N`
- **Phase 1 branches from the current branch** (the branch where the PRD is being worked on, not necessarily main)
- Phase N branches from Phase N-1's branch (creating a chain: current branch → phase-1 → phase-2 → phase-3...)
- Aim for phases that can be reviewed in a single PR without being overwhelming
- **Each phase must include the three Quality Assurance stories** (Code Review, Security Review, Test Review) at the end of that phase's stories
- When using phases, renumber QA stories for each phase (e.g., US-007/008/009 for Phase 1, US-010/011/012 for Phase 2)
- Security reports should be phase-specific (e.g., `security-report-phase-1.md`, `security-report-phase-2.md`)
- **Natural phase boundaries:**
  - Database/schema changes → API/backend logic → UI components
  - Core functionality → Advanced features → Polish/optimization
  - Single area of codebase → Integration with other areas

### 4. User Stories
Each story needs:
- **Title:** Short descriptive name
- **Description:** "As a [user], I want [feature] so that [benefit]"
- **Acceptance Criteria:** Verifiable checklist of what "done" means

Each story should be small enough to implement in one focused session.

**If using phases:** Group stories under their respective phase sections. If not using phases, list all stories in a single "User Stories" section.

**Format:**
```markdown
### US-001: [Title]
**Description:** As a [user], I want [feature] so that [benefit].

**Acceptance Criteria:**
- [ ] Write failing test(s) first (TDD Red phase)
- [ ] Implement minimal code to pass tests (TDD Green phase)
- [ ] Refactor code while keeping tests passing (TDD Refactor phase)
- [ ] Specific verifiable criterion
- [ ] Another criterion
- [ ] Typecheck/lint passes
- [ ] **[UI stories only]** Verify in browser using dev-browser skill
```

**Important:** 
- **Test Driven Development (TDD) is required:** All implementation stories must follow the Red-Green-Refactor cycle:
  1. **Red:** Write failing test(s) first that define the desired behavior
  2. **Green:** Write the minimum code needed to make tests pass
  3. **Refactor:** Improve code quality while keeping all tests passing
- Acceptance criteria must be verifiable, not vague. "Works correctly" is bad. "Button shows confirmation dialog before deleting" is good.
- **For any story with UI changes:** Always include "Verify in browser using dev-browser skill" as acceptance criteria. This ensures visual verification of frontend work.
- Tests should be written BEFORE implementation code, not after. This ensures tests actually test the code and prevents over-engineering.

**Required Quality Assurance Stories:**
Every PRD must include these three reviewer stories. These specialists ensure code quality, security, and test coverage:

- **If using phases:** Include these three QA stories at the end of EACH phase (renumbered for each phase)
- **If not using phases:** Include these three QA stories at the end of the User Stories section

### US-XXX: Code Review - Edge Case Analysis
**Description:** As a code reviewer specialist, I want to review all changes in the branch for potential edge case bugs so that critical issues are fixed and non-critical ones are documented.

**Acceptance Criteria:**
- [ ] Review all code changes in the branch for edge cases
- [ ] Fix all critical edge case bugs found
- [ ] Document non-critical edge cases in markdown format
- [ ] Follow best practices for code review and edge case analysis
- [ ] Typecheck/lint passes

### US-XXX: Security Review - Production Hardening
**Description:** As a code security specialist, I want to review all code created/modified in the branch for security vulnerabilities so that the code is hardened for production use. I want to fix critical issues found, write a report on critical issues that were found/fixed. I don't want to fix the medium and minor issues, but we do wnat to document them.

**Acceptance Criteria:**
- [ ] Review all code created/modified in the branch for security vulnerabilities
- [ ] Identify and fix security issues (SQL injection, XSS, CSRF, auth flaws, etc.)
- [ ] Ensure proper input validation and sanitization
- [ ] Verify secure handling of sensitive data
- [ ] Follow security best practices and OWASP guidelines
- [ ] Typecheck/lint passes
- [ ] Security report is written/saved to `tasks/feature-name/security-report.md` (or `security-report-phase-N.md` if using phases)

### US-XXX: Test Review - Quality Assurance
**Description:** As a test-driven development specialist, I want to review all tests in the branch to ensure they follow TDD best practices, are comprehensive, not "cheated", and cover normal use cases and all known edge cases. And fix any issues found.

**Acceptance Criteria:**
- [ ] Verify TDD workflow was followed: tests were written BEFORE implementation code (Red-Green-Refactor cycle)
- [ ] Review all tests created/modified in the branch
- [ ] Verify tests are not "cheated" (no false positives, proper assertions), like skipping tests or deleting tests that are relevant to the changes, or writing tests that are not relevant to the changes
- [ ] Ensure tests were written first and failed initially (Red phase), then implementation made them pass (Green phase)
- [ ] Verify no implementation code exists without corresponding tests
- [ ] Ensure tests cover normal use cases
- [ ] Ensure tests cover all known edge cases
- [ ] Verify test quality follows TDD best practices (tests define behavior, not just verify implementation)
- [ ] Confirm tests are maintainable and well-structured
- [ ] Typecheck/lint passes
```

**Note:** Replace `US-XXX` with the appropriate sequential story number based on your total story count.

### 5. Functional Requirements
Numbered list of specific functionalities:
- "FR-1: The system must allow users to..."
- "FR-2: When a user clicks X, the system must..."

Be explicit and unambiguous.

### 6. Non-Goals (Out of Scope)
What this feature will NOT include. Critical for managing scope.

### 7. Design Considerations (Optional)
- UI/UX requirements
- Link to mockups if available
- Relevant existing components to reuse

### 8. Technical Considerations (Optional)
- Known constraints or dependencies
- Integration points with existing systems
- Performance requirements

### 9. Success Metrics
How will success be measured?
- "Reduce time to complete X by 50%"
- "Increase conversion rate by 10%"

### 10. Open Questions
Remaining questions or areas needing clarification.

---

## Test Driven Development (TDD) Requirements

**All implementation stories MUST follow TDD best practices:**

1. **Red Phase:** Write failing test(s) first
   - Tests define the desired behavior before any implementation
   - Tests should fail initially (this proves they're testing something)
   - Focus on what the code should do, not how it does it

2. **Green Phase:** Write minimal implementation
   - Only write enough code to make the tests pass
   - Avoid over-engineering or adding features not covered by tests
   - Keep it simple and focused

3. **Refactor Phase:** Improve code quality
   - Clean up, remove duplication, improve design
   - All tests must still pass after refactoring
   - Improve readability and maintainability

**Why TDD?**
- Tests written first ensure they actually test the code (not just verify implementation)
- Prevents over-engineering by focusing on what's needed
- Better design emerges from writing testable code
- Tests serve as documentation of expected behavior
- Catches bugs earlier in the development cycle

## Writing for Junior Developers

The PRD reader may be a junior developer or AI agent. Therefore:

- Be explicit and unambiguous
- Avoid jargon or explain it
- Provide enough detail to understand purpose and core logic
- Number requirements for easy reference
- Use concrete examples where helpful
- **Emphasize TDD workflow:** Tests first, then implementation, then refactor

---

## Output

- **Format:** Markdown (`.md`)
- **Location:** `tasks/`
- **Filename:** `prd-[feature-name].md` (kebab-case)

---

## Example PRD

```markdown
# PRD: Task Priority System

## Introduction

Add priority levels to tasks so users can focus on what matters most. Tasks can be marked as high, medium, or low priority, with visual indicators and filtering to help users manage their workload effectively.

## Goals

- Allow assigning priority (high/medium/low) to any task
- Provide clear visual differentiation between priority levels
- Enable filtering and sorting by priority
- Default new tasks to medium priority

## User Stories

### US-001: Add priority field to database
**Description:** As a developer, I need to store task priority so it persists across sessions.

**Acceptance Criteria:**
- [ ] Write failing test(s) first (TDD Red phase) - test that priority field exists and defaults to 'medium'
- [ ] Implement minimal code to pass tests (TDD Green phase) - add priority column to tasks table: 'high' | 'medium' | 'low' (default 'medium')
- [ ] Refactor code while keeping tests passing (TDD Refactor phase)
- [ ] Generate and run migration successfully
- [ ] Typecheck passes

### US-002: Display priority indicator on task cards
**Description:** As a user, I want to see task priority at a glance so I know what needs attention first.

**Acceptance Criteria:**
- [ ] Write failing test(s) first (TDD Red phase) - test that task cards render priority badges with correct colors
- [ ] Implement minimal code to pass tests (TDD Green phase) - add priority badge component to task cards
- [ ] Refactor code while keeping tests passing (TDD Refactor phase)
- [ ] Each task card shows colored priority badge (red=high, yellow=medium, gray=low)
- [ ] Priority visible without hovering or clicking
- [ ] Typecheck passes
- [ ] Verify in browser using dev-browser skill

### US-003: Add priority selector to task edit
**Description:** As a user, I want to change a task's priority when editing it.

**Acceptance Criteria:**
- [ ] Write failing test(s) first (TDD Red phase) - test priority selector behavior and save functionality
- [ ] Implement minimal code to pass tests (TDD Green phase) - add priority dropdown to edit modal
- [ ] Refactor code while keeping tests passing (TDD Refactor phase)
- [ ] Priority dropdown in task edit modal
- [ ] Shows current priority as selected
- [ ] Saves immediately on selection change
- [ ] Typecheck passes
- [ ] Verify in browser using dev-browser skill

### US-004: Filter tasks by priority
**Description:** As a user, I want to filter the task list to see only high-priority items when I'm focused.

**Acceptance Criteria:**
- [ ] Write failing test(s) first (TDD Red phase) - test filtering logic and URL param persistence
- [ ] Implement minimal code to pass tests (TDD Green phase) - add filter dropdown and filtering logic
- [ ] Refactor code while keeping tests passing (TDD Refactor phase)
- [ ] Filter dropdown with options: All | High | Medium | Low
- [ ] Filter persists in URL params
- [ ] Empty state message when no tasks match filter
- [ ] Typecheck passes
- [ ] Verify in browser using dev-browser skill

## Functional Requirements

- FR-1: Add `priority` field to tasks table ('high' | 'medium' | 'low', default 'medium')
- FR-2: Display colored priority badge on each task card
- FR-3: Include priority selector in task edit modal
- FR-4: Add priority filter dropdown to task list header
- FR-5: Sort by priority within each status column (high to medium to low)

## Non-Goals

- No priority-based notifications or reminders
- No automatic priority assignment based on due date
- No priority inheritance for subtasks

## Technical Considerations

- Reuse existing badge component with color variants
- Filter state managed via URL search params
- Priority stored in database, not computed

## Success Metrics

- Users can change priority in under 2 clicks
- High-priority tasks immediately visible at top of lists
- No regression in task list performance

## Open Questions

- Should priority affect task ordering within a column?
- Should we add keyboard shortcuts for priority changes?
```

---

## Checklist

Before saving the PRD:

- [ ] Asked clarifying questions with lettered options
- [ ] Incorporated user's answers
- [ ] **Created phases if feature is large** (6+ stories, 10+ files, or spans multiple codebase areas)
- [ ] If using phases, each phase has clear description and branch name
- [ ] If not using phases, feature is small enough (3-4 stories, 2-3 files) to skip phases
- [ ] User stories are small and specific
- [ ] **All implementation stories include TDD acceptance criteria** (Red-Green-Refactor phases)
- [ ] Functional requirements are numbered and unambiguous
- [ ] Non-goals section defines clear boundaries
- [ ] **Included the three required Quality Assurance reviewer stories** (Code Review, Security Review, Test Review)
- [ ] **If using phases, QA stories are included in EACH phase** (renumbered appropriately)
- [ ] Test Review story emphasizes TDD workflow verification
- [ ] Saved to `tasks/prd-[feature-name].md`
