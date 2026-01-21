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

Ask only critical questions where the initial prompt is ambiguous. **Only ask about context if the work type is unclear from the description.**

### Determining Work Type

**Skip the context question if the description clearly indicates:**
- **Product development:** Mentions UI, APIs, features, user-facing functionality, application code, etc.
- **Infrastructure as code:** Mentions Terraform, CloudFormation, Kubernetes, RDS, S3, infrastructure provisioning, etc.
- **DevOps/CI/CD:** Mentions pipelines, automation, deployment tooling, etc.

**Only ask the context question if:** The description is ambiguous and could be interpreted as multiple types of work.

### Question Focus Areas

- **Context (if needed):** Is this product development or infrastructure as code? (Only ask if unclear from description)
- **Problem/Goal:** What problem does this solve?
- **Core Functionality:** What are the key actions?
- **Scope/Boundaries:** What should it NOT do?
- **Success Criteria:** How do we know it's done?

### Scope Assessment

**While asking questions, also assess scope:**
- How many files will this likely touch? (database, API, UI, etc.)
- How many distinct areas of the codebase?
- Does this span backend and frontend?
- Based on this, determine if phases will be needed (see Phase Guidelines below)

### Infrastructure-Specific Questions

**For infrastructure as code:** If the work type is determined to be infrastructure as code (either from the description or from the context question), ask about plan checks and real-world validation. By default, infrastructure uses validation and code review only (no plan checks or deployment).

### Question Format Template

**If context is unclear, start with the context question. Otherwise, start with other clarifying questions.**

Format questions with clear spacing between each question and its options. Use this structure:

---

**Example 1: When context is unclear (include context question):**

**1. What type of work is this?**
   - **A.** Product development (application features, APIs, UI)
   - **B.** Infrastructure as code (Terraform, CloudFormation, Kubernetes, etc.)
   - **C.** DevOps/CI/CD (pipelines, automation, tooling)
   - **D.** Other: [please specify]

**2. What is the primary goal of this feature?**
   - **A.** Improve user onboarding experience
   - **B.** Increase user retention
   - **C.** Reduce support burden
   - **D.** Provision/manage infrastructure
   - **E.** Other: [please specify]

**3. Who is the target user?**
   - **A.** End users of the application
   - **B.** Developers/engineers
   - **C.** System administrators
   - **D.** All of the above
   - **E.** Other: [please specify]

**4. What is the scope?**
   - **A.** Minimal viable version
   - **B.** Full-featured implementation
   - **C.** Just the backend/API
   - **D.** Just the UI
   - **E.** Just the infrastructure layer

**5. [If infrastructure as code] Do you need plan checks (terraform plan, etc.)?**
   - **A.** No, validation and code review are sufficient
   - **B.** Yes, run plan checks to preview changes (requires cloud provider auth)
   - **C.** Not sure

**6. [If infrastructure as code] Do you need real-world validation (deploy to test environment)?**
   - **A.** No, validation and code review (and plan checks if requested) are sufficient
   - **B.** Yes, deploy to test environment and verify actual resources (includes plan checks)
   - **C.** Not sure

---

**Example 2: When context is clear (skip context question):**

**1. What is the primary goal of this feature?**
   - **A.** Improve user onboarding experience
   - **B.** Increase user retention
   - **C.** Reduce support burden
   - **D.** Other: [please specify]

**2. Who is the target user?**
   - **A.** End users of the application
   - **B.** Developers/engineers
   - **C.** System administrators
   - **D.** All of the above
   - **E.** Other: [please specify]

**3. What is the scope?**
   - **A.** Minimal viable version
   - **B.** Full-featured implementation
   - **C.** Just the backend/API
   - **D.** Just the UI
   - **E.** Other: [please specify]

**4. [If infrastructure as code] Do you need plan checks (terraform plan, etc.)?**
   - **A.** No, validation and code review are sufficient
   - **B.** Yes, run plan checks to preview changes (requires cloud provider auth)
   - **C.** Not sure

**5. [If infrastructure as code] Do you need real-world validation (deploy to test environment)?**
   - **A.** No, validation and code review (and plan checks if requested) are sufficient
   - **B.** Yes, deploy to test environment and verify actual resources (includes plan checks)
   - **C.** Not sure

---

**Response format:** Users can respond with "1A, 2C, 3B" for quick iteration.

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

**Format (Product Development):**
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

**Format (Infrastructure as Code - Default):**
```markdown
### US-001: [Title]
**Description:** As a [user], I want [feature] so that [benefit].

**Acceptance Criteria:**
- [ ] Validate infrastructure code (terraform validate, cfn-lint, etc.)
- [ ] Verify infrastructure code matches requirements (specific checks)
- [ ] Run security/compliance scans on code (if applicable)
- [ ] Typecheck/lint passes
```

**Format (Infrastructure as Code - With Plan Checks):**
*Only use this format when plan checks are explicitly requested. Plan checks require cloud provider authentication.*

```markdown
### US-001: [Title]
**Description:** As a [user], I want [feature] so that [benefit].

**Acceptance Criteria:**
- [ ] Validate infrastructure code (terraform validate, cfn-lint, etc.)
- [ ] Run plan/dry-run check (terraform plan, etc.) and verify expected changes match requirements
- [ ] Verify infrastructure code matches requirements (specific checks)
- [ ] Run security/compliance scans on code (if applicable)
- [ ] Typecheck/lint passes
```

**Format (Infrastructure as Code - With Real-World Validation):**
*Only use this format when real-world validation is explicitly requested or required. This includes plan checks since deployment requires them.*

```markdown
### US-001: [Title]
**Description:** As a [user], I want [feature] so that [benefit].

**Acceptance Criteria:**
- [ ] Validate infrastructure code (terraform validate, cfn-lint, etc.)
- [ ] Run plan/dry-run check (terraform plan, etc.) and verify expected changes
- [ ] Deploy to test environment and verify resources are created correctly
- [ ] Verify infrastructure matches requirements (specific checks)
- [ ] Run security/compliance scans (if applicable)
- [ ] Document any manual verification steps performed
- [ ] Typecheck/lint passes
```

**Important:** 
- **For Product Development:** Test Driven Development (TDD) is required. All implementation stories must follow the Red-Green-Refactor cycle:
  1. **Red:** Write failing test(s) first that define the desired behavior
  2. **Green:** Write the minimum code needed to make tests pass
  3. **Refactor:** Improve code quality while keeping all tests passing
- **For Infrastructure as Code:** Testing follows a validation and code review approach:
  1. **Validate:** Use infrastructure tooling validation (terraform validate, CloudFormation validation, etc.)
  2. **Code Review:** Verify infrastructure code matches requirements (resource properties, configurations, etc.)
  3. **Security/Compliance:** Run security scans on infrastructure code (not actual infrastructure unless specified)
  
  **Plan checks (terraform plan, etc.) require cloud provider authentication and are only used when explicitly requested.**
  
  **Real-world validation (deploy to test environment) is only used when explicitly requested or required.** By default, infrastructure as code uses validation and code review only.
- Acceptance criteria must be verifiable, not vague. "Works correctly" is bad. "Button shows confirmation dialog before deleting" or "EC2 instance has t3.medium instance type" is good.
- **For any story with UI changes:** Always include "Verify in browser using dev-browser skill" as acceptance criteria. This ensures visual verification of frontend work.
- **For product development:** Tests should be written BEFORE implementation code, not after. This ensures tests actually test the code and prevents over-engineering.
- **For infrastructure as code:** Validation and plan checks should be run before deployment, but actual verification happens in real environments.

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
**Description:** As a quality assurance specialist, I want to review all tests and validation in the branch to ensure they follow best practices, are comprehensive, not "cheated", and cover normal use cases and all known edge cases. And fix any issues found.

**Acceptance Criteria (Product Development):**
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

**Acceptance Criteria (Infrastructure as Code - Default):**
- [ ] Verify all infrastructure code has validation checks (terraform validate, cfn-lint, etc.)
- [ ] Verify infrastructure code matches requirements (resource properties, configurations, etc.)
- [ ] Verify security/compliance scans were run on code (if applicable)
- [ ] Ensure edge cases are considered in code review (e.g., resource already exists, insufficient permissions, region availability)
- [ ] Verify no infrastructure code exists without corresponding validation
- [ ] Confirm validation steps are documented and repeatable
- [ ] Typecheck/lint passes

**Acceptance Criteria (Infrastructure as Code - With Plan Checks):**
*Only use these criteria when plan checks were explicitly requested.*

- [ ] Verify all infrastructure code has validation checks (terraform validate, cfn-lint, etc.)
- [ ] Review all plan/dry-run outputs to ensure expected changes are correct and match requirements
- [ ] Verify infrastructure code matches requirements (resource properties, configurations, etc.)
- [ ] Verify security/compliance scans were run on code (if applicable)
- [ ] Ensure edge cases are covered in plan checks (e.g., resource already exists, insufficient permissions, region availability)
- [ ] Verify no infrastructure code exists without corresponding validation/plan checks
- [ ] Confirm validation and plan steps are documented and repeatable
- [ ] Typecheck/lint passes

**Acceptance Criteria (Infrastructure as Code - With Real-World Validation):**
*Only use these criteria when real-world validation was explicitly requested or required. This includes plan checks since deployment requires them.*

- [ ] Verify all infrastructure code has validation checks (terraform validate, cfn-lint, etc.)
- [ ] Review all plan/dry-run outputs to ensure expected changes are correct
- [ ] Verify test environment deployments were performed and documented
- [ ] Ensure real-world verification checks are comprehensive (verify actual resource properties, not just that resources exist)
- [ ] Verify security/compliance scans were run on actual infrastructure (if applicable)
- [ ] Ensure edge cases are covered (e.g., resource already exists, insufficient permissions, region availability)
- [ ] Verify no infrastructure code exists without corresponding validation/verification
- [ ] Confirm validation and verification steps are documented and repeatable
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

## Testing Requirements

### Product Development: Test Driven Development (TDD)

**All product development implementation stories MUST follow TDD best practices:**

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

**Why TDD for Product Development?**
- Tests written first ensure they actually test the code (not just verify implementation)
- Prevents over-engineering by focusing on what's needed
- Better design emerges from writing testable code
- Tests serve as documentation of expected behavior
- Catches bugs earlier in the development cycle

### Infrastructure as Code: Validation and Code Review

**Infrastructure as code follows a validation and code review approach:**

1. **Validation Phase:** Validate infrastructure code
   - Run tool-specific validation (terraform validate, CloudFormation validation, Ansible validation, etc.)
   - Check syntax, references, and basic correctness
   - Fix any validation errors before proceeding

2. **Code Review Phase:** Verify code matches requirements
   - Review infrastructure code to ensure resource configurations match requirements
   - Verify security settings, encryption, access controls, etc. are correctly specified
   - Run security/compliance scans on infrastructure code (not actual infrastructure)

**Plan Checks (Optional):**
*Only use plan checks when explicitly requested. Plan checks require cloud provider authentication.*

3. **Plan Phase:** Preview changes (if requested)
   - Run plan/dry-run checks (terraform plan, etc.)
   - Review expected changes to ensure they match requirements
   - Verify no unexpected changes or resource destruction
   - Check that resource properties in plan match requirements

**Real-World Validation (Optional):**
*Only use real-world validation when explicitly requested or required. This includes plan checks since deployment requires them.*

4. **Deploy & Verify Phase:** Deploy to test environment (if requested)
   - Deploy infrastructure to a test/staging environment
   - Verify resources are actually created with correct properties
   - Check real-world state matches requirements (instance types, encryption settings, etc.)
   - Run security/compliance scans on actual infrastructure

5. **Documentation Phase:** Document verification (if real-world validation was performed)
   - Document what was verified and how
   - Note any manual verification steps performed
   - Record test environment details for reproducibility

**Why Validation and Code Review for Infrastructure?**
- Validation catches syntax and reference errors early
- Code review ensures infrastructure code correctly specifies desired state
- Security/compliance scans on code catch issues before deployment
- **Plan checks require cloud provider authentication and are only used when explicitly requested**
- **Real-world validation is only needed when you need to verify actual infrastructure behavior or when explicitly requested**

## Writing for Junior Developers

The PRD reader may be a junior developer or AI agent. Therefore:

- Be explicit and unambiguous
- Avoid jargon or explain it
- Provide enough detail to understand purpose and core logic
- Number requirements for easy reference
- Use concrete examples where helpful
- **For product development:** Emphasize TDD workflow (tests first, then implementation, then refactor)
- **For infrastructure as code:** Emphasize validation → code review workflow (plan checks and real-world validation only if explicitly requested)
- Clearly distinguish between product development and infrastructure as code contexts

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

### Example PRD: Infrastructure as Code

```markdown
# PRD: Production Database Infrastructure

## Introduction

Provision a production-ready PostgreSQL database on AWS RDS with proper security, backup, and monitoring configuration. This infrastructure will support our main application database needs with high availability and automated backups.

## Goals

- Provision RDS PostgreSQL instance with appropriate instance type
- Configure automated backups with 7-day retention
- Enable encryption at rest and in transit
- Set up VPC security groups for database access
- Configure CloudWatch monitoring and alarms
- Document connection details and access patterns

## User Stories

### US-001: Create RDS PostgreSQL instance
**Description:** As a DevOps engineer, I need a production PostgreSQL database so the application can store and retrieve data reliably.

**Acceptance Criteria:**
- [ ] Validate Terraform code (terraform validate passes)
- [ ] Verify infrastructure code defines RDS instance with engine version PostgreSQL 15.4
- [ ] Verify infrastructure code defines instance type as db.t3.medium
- [ ] Verify infrastructure code places instance in correct VPC and subnets
- [ ] Verify infrastructure code enables multi-AZ deployment
- [ ] Verify infrastructure code matches all requirements
- [ ] Typecheck/lint passes

### US-002: Configure automated backups
**Description:** As a DevOps engineer, I need automated daily backups so we can recover from data loss incidents.

**Acceptance Criteria:**
- [ ] Validate Terraform code (terraform validate passes)
- [ ] Verify infrastructure code sets backup retention period to 7 days
- [ ] Verify infrastructure code sets backup window to off-peak hours (03:00-04:00 UTC)
- [ ] Verify infrastructure code enables automated backups
- [ ] Verify infrastructure code matches all requirements
- [ ] Typecheck/lint passes

### US-003: Enable encryption and security
**Description:** As a security engineer, I need the database encrypted so sensitive data is protected at rest and in transit.

**Acceptance Criteria:**
- [ ] Validate Terraform code (terraform validate passes)
- [ ] Verify infrastructure code enables encryption at rest (KMS key)
- [ ] Verify infrastructure code enforces SSL/TLS encryption in transit
- [ ] Verify security group configuration only allows connections from application servers
- [ ] Run security scan on Terraform code (checkov, tfsec, etc.) and verify no critical issues
- [ ] Verify infrastructure code matches all requirements
- [ ] Typecheck/lint passes

### US-004: Set up CloudWatch monitoring
**Description:** As a DevOps engineer, I need database monitoring and alarms so I can detect issues before they impact users.

**Acceptance Criteria:**
- [ ] Validate Terraform code (terraform validate passes)
- [ ] Verify infrastructure code defines CloudWatch resources (alarms, dashboards)
- [ ] Verify infrastructure code configures CPU utilization alarm (threshold: 80%)
- [ ] Verify infrastructure code configures free storage space alarm (threshold: 20% free)
- [ ] Verify infrastructure code configures connection count alarm (threshold: 80% of max)
- [ ] Verify infrastructure code configures alarms to send notifications to SNS topic
- [ ] Verify infrastructure code matches all requirements
- [ ] Typecheck/lint passes

## Functional Requirements

- FR-1: RDS PostgreSQL 15.4 instance with db.t3.medium instance type
- FR-2: Multi-AZ deployment enabled for high availability
- FR-3: Automated daily backups with 7-day retention
- FR-4: Encryption at rest using AWS KMS
- FR-5: SSL/TLS encryption in transit enforced
- FR-6: Security group restricting access to application subnet only
- FR-7: CloudWatch alarms for CPU, storage, and connections
- FR-8: Parameter group with production-optimized settings

## Non-Goals

- No read replicas (out of scope for initial implementation)
- No cross-region backup replication
- No automated failover testing (manual process)
- No database migration tooling

## Technical Considerations

- Use existing VPC and subnets (do not create new VPC)
- Reuse existing KMS key for encryption
- Integrate with existing SNS topic for alarm notifications
- Follow company Terraform module structure and naming conventions
- Store connection credentials in AWS Secrets Manager (separate story)

## Success Metrics

- Validation passes without errors
- Security scans on code show no critical issues
- Infrastructure code matches all requirements
- Infrastructure code can be validated and reviewed without errors

## Open Questions

- Should we use provisioned IOPS or standard storage?
- What is the expected connection count for capacity planning?
- Do we need a maintenance window preference?
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
- [ ] Test Review story emphasizes appropriate testing workflow verification (TDD for product, validation/code review for infrastructure by default)
- [ ] Saved to `tasks/prd-[feature-name].md`
