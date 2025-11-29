# GitHub Templates Reference

This document describes the GitHub templates created for Stonks Overwatch to facilitate community contributions and issue tracking.

## Created Templates

### Issue Templates

Located in `.github/ISSUE_TEMPLATE/`

#### 1. Bug Report (`bug_report.md`)

**Purpose:** Simple, streamlined format for reporting bugs

**Includes:**
- What happened (bug description)
- Steps to reproduce
- Expected vs actual behavior (combined)
- Environment info (OS, Python, brokers, app type)
- Logs section (optional)
- Quick reminder to check FAQ

**Key Features:**
- **Minimal and focused** - Only essential information
- **Easy to complete** - No overwhelming checklists
- **Quick reminder** - Simple tip to check FAQ before submitting
- **Reduced friction** - Users won't drop off due to complexity

**URL:** `https://github.com/ctasada/stonks-overwatch/issues/new?template=bug_report.md`

#### 2. Feature Request (`feature_request.md`)

**Purpose:** Simple format for proposing new features

**Includes:**
- What feature (brief description)
- Why useful (problem it solves)
- How it should work (idea)
- Additional info (broker-specific, priority)

**Key Features:**
- **Ultra-simplified** - Only 4 main sections
- **No overwhelming fields** - Removed optional sections like alternatives, implementation ideas, mockups
- **Quick to complete** - Users can submit in minutes, not hours
- **Still captures essentials** - Gets the information needed without friction

**URL:** `https://github.com/ctasada/stonks-overwatch/issues/new?template=feature_request.md`

#### 3. Question (`question.md`)

**Purpose:** Simple format for asking questions

**Includes:**
- Question text
- What you've tried (minimal checklist)
- Quick tip about GitHub Discussions

**Key Features:**
- **Minimal checklist** - Only 3 essential items
- **No unnecessary fields** - Removed environment, context sections
- **Quick tip** - Suggests Discussions for general questions
- **Fast to complete** - Users can ask questions without barriers

**URL:** `https://github.com/ctasada/stonks-overwatch/issues/new?template=question.md`

#### 4. Config (`config.yml`)

**Purpose:** Configure issue template chooser and provide quick links

**Includes:**
- Link to GitHub Discussions
- Link to Documentation
- Link to FAQ
- Enables blank issues

### Pull Request Template

Located at `.github/PULL_REQUEST_TEMPLATE.md`

**Purpose:** Ultra-simplified format for pull requests

**Key Features:**
- **Minimal and focused** - Only essential sections
- **Consolidated checklists** - Combined testing and quality into one section
- **Quick to complete** - No overwhelming fields
- **Reduced friction** - Users won't drop off due to complexity

**Includes:**
- Description
- Type of change (simplified labels)
- Related issues
- Changes made
- Testing & Quality (combined, 3 essential checks)
- Screenshots (if applicable)
- Simple checklist reminder

**Removed:**
- Separate "Testing" and "Code Quality" sections → Combined
- Verbose checklists → Reduced to essentials
- "Breaking Changes" section → Can be mentioned in description
- Redundant checklist items → Single reminder at bottom

## Usage

### For Contributors

When creating an issue or PR, GitHub will automatically present the appropriate template. Simply fill in the sections with your information.

### For Maintainers

Templates ensure consistent, high-quality submissions that include all necessary information for review and triage.

## Benefits

✅ **User-friendly** - Simple, focused templates that don't overwhelm users
✅ **Low friction** - Easy to complete, reducing drop-off rates
✅ **Consistency** - All issues/PRs have the same structure
✅ **Faster triage** - Maintainers can quickly assess issues
✅ **Better quality** - Guides contributors to provide essential details without burden
✅ **Professional appearance** - Shows project maturity

## Customization

These templates can be customized as the project evolves:

1. Edit template files in `.github/ISSUE_TEMPLATE/` and `.github/`
2. Add new templates for specific issue types
3. Update config.yml to add more quick links
4. Adjust required information based on common gaps

## Testing Templates

To test templates locally before pushing:

1. Create a test issue/PR on GitHub
2. Verify template appears correctly
3. Check all links work
4. Ensure formatting is correct
5. Validate required sections are clear

---

**Created**: November 19, 2025
**Status**: Active
