# GitHub Templates Reference

This document describes the GitHub templates created for Stonks Overwatch to facilitate community contributions and issue tracking.

## Created Templates

### Issue Templates

Located in `.github/ISSUE_TEMPLATE/`

#### 1. Bug Report (`bug_report.md`)

**Purpose:** Standardized format for reporting bugs

**Includes:**
- Bug description
- Steps to reproduce
- Expected vs actual behavior
- Environment information (OS, Python version, etc.)
- Configuration details (which brokers)
- Log output section
- Checklist for reporters

**URL:** `https://github.com/ctasada/stonks-overwatch/issues/new?template=bug_report.md`

#### 2. Feature Request (`feature_request.md`)

**Purpose:** Structured format for proposing new features

**Includes:**
- Feature description
- Problem statement
- Proposed solution
- Alternative solutions
- Use cases
- Implementation ideas
- Priority level
- Broker-specific tag
- Checklist for requesters

**URL:** `https://github.com/ctasada/stonks-overwatch/issues/new?template=feature_request.md`

#### 3. Question (`question.md`)

**Purpose:** Format for asking questions (alternative to Discussions)

**Includes:**
- Question text
- Context
- What you've already tried
- Environment (if relevant)
- Links to documentation

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

**Purpose:** Standardized format for pull requests

**Includes:**
- Description section
- Type of change checkboxes (bug fix, feature, docs, etc.)
- Related issues linking
- Testing performed checklist
- Code quality checklist
- Documentation updates
- Screenshots for UI changes
- Breaking changes section
- Deployment notes
- Comprehensive checklist

## Usage

### For Contributors

When creating an issue or PR, GitHub will automatically present the appropriate template. Simply fill in the sections with your information.

### For Maintainers

Templates ensure consistent, high-quality submissions that include all necessary information for review and triage.

## Benefits

✅ **Consistency** - All issues/PRs have the same structure
✅ **Completeness** - Templates prompt for all necessary information
✅ **Faster triage** - Maintainers can quickly assess issues
✅ **Better quality** - Guides contributors to provide useful details
✅ **Documentation links** - Templates reference relevant docs
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
