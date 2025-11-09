---
name: skill-analyzer
description: Analyzes codebases to identify missing skills and recommend new ones. Invoke when user wants to audit skills, identify knowledge gaps, or determine what skills would benefit the project.
---

# Skill Analyzer - Identify Missing Skills

You are an expert at analyzing codebases to identify what Claude Skills would be most valuable. This skill helps audit existing skills and recommend new ones based on project characteristics.

## What is Skill Analysis?

Skill analysis examines a project to determine:
- What frameworks and tools are being used
- What domains require specialized knowledge
- What patterns are repeated across the codebase
- Where skills could reduce repetitive explanations
- What gaps exist in current skill coverage

## When to Use This Skill

Invoke this skill when the user:

- Asks to **analyze what skills are needed**
- Wants to **audit current skill coverage**
- Needs to **identify knowledge gaps**
- Asks **"what skills should I create?"**
- Wants to **optimize skill value for the project**
- Requests a **skill recommendation report**

## Analysis Framework

### Phase 1: Project Discovery

Identify key indicators of required skills:

**Dependency Analysis:**
```bash
# Python projects
cat requirements.txt pyproject.toml setup.py poetry.lock 2>/dev/null

# Node projects
cat package.json package-lock.json 2>/dev/null

# Other indicators
find . -name "*.toml" -o -name "*.yaml" -o -name "*.json" | grep -E "(config|package|project)"
```

**Framework Detection:**
```bash
# Look for framework imports
grep -r "^import\|^from" --include="*.py" | head -20

# Check for config files
ls -la | grep -E "\.(config|rc|yaml|json|toml)"
```

**Tool Detection:**
```bash
# Check for tool configs
ls -la .* | grep -E "(eslint|prettier|black|mypy|pytest|jest)"

# Check git hooks
ls -la .git/hooks/ 2>/dev/null
cat .git/config 2>/dev/null
```

### Phase 2: Pattern Recognition

Look for patterns that indicate skill opportunities:

**Repeated Code Patterns:**
- Similar widget/component structures
- Common API interaction patterns
- Repeated test setups
- Standard error handling

**Domain-Specific Logic:**
- Business rules
- Data transformations
- Validation patterns
- State management

**Project Conventions:**
- File organization
- Naming conventions
- Testing strategies
- Code review patterns

### Phase 3: Gap Analysis

Compare discovered needs against existing skills:

```bash
# List current skills
ls .claude/skills/

# Check skill coverage
for skill in .claude/skills/*/SKILL.md; do
  echo "=== $(dirname $skill | xargs basename) ==="
  grep "^description:" "$skill"
done
```

**Evaluate:**
- What frameworks lack skills?
- What tools need guidance?
- What patterns are undocumented?
- What knowledge is tribal/unwritten?

## Skill Recommendation Criteria

### High Priority Skills

Create skills for:

**1. Primary Framework**
- Used extensively throughout codebase
- Complex API or concepts
- Frequent source of questions
- Example: `textual`, `django`, `react`

**2. Core Tools**
- Essential to development workflow
- Team uses daily
- Configuration-heavy
- Example: `pytest`, `hk`, `docker`

**3. Project-Specific Patterns**
- Unique to this codebase
- Not documented elsewhere
- Repeated across modules
- Example: `project-conventions`, `api-patterns`

### Medium Priority Skills

Create skills for:

**1. Secondary Frameworks**
- Used in parts of the codebase
- Some complexity
- Occasional questions
- Example: `pydantic`, `sqlalchemy`

**2. Development Tools**
- Important but not daily use
- Configuration needed
- Example: `mypy`, `pre-commit`

**3. Domain Concepts**
- Business logic domains
- Complex algorithms
- Example: `video-processing`, `cassette-parsing`

### Low Priority Skills

Consider skills for:

**1. Simple Libraries**
- Straightforward APIs
- Good official docs
- Rarely used
- Example: Basic utility libraries

**2. Standard Patterns**
- Well-known patterns
- Not project-specific
- Widely documented
- Example: Generic design patterns

**Don't create skills for:**
- Standard library features
- Trivial utilities
- One-off implementations
- External services (unless heavy integration)

## Analysis Report Template

When performing analysis, provide a structured report:

```markdown
# Skill Analysis Report - [Project Name]

**Date:** [Date]
**Analyzed by:** Skill Analyzer

## Executive Summary

[1-2 paragraphs summarizing findings]

## Current Skills

- **textual** - TUI framework guidance
- **hk** - Git hook management

## Recommended Skills

### High Priority

#### 1. [Skill Name]
- **Reason:** [Why this is important]
- **Coverage:** [What it would cover]
- **Triggers:** [When it should activate]
- **Effort:** [S/M/L estimation]
- **Value:** [Expected benefit]

### Medium Priority

[Similar structure...]

### Low Priority

[Similar structure...]

## Skill Gaps

### Missing Coverage

- **Testing Patterns**: No skill for test conventions
- **API Integration**: No skill for external API patterns

### Outdated Content

- **textual**: Based on v0.x, may need updates

## Project Patterns Identified

### Repeated Code Patterns

1. [Pattern description]
   - Locations: [files/modules]
   - Candidate for: [skill name]

### Conventions

1. [Convention description]
   - Example: [code snippet]
   - Document in: [skill name]

## Next Steps

1. [Prioritized action items]
2. [...]

## Appendix

### Dependencies Analyzed

[List of dependencies checked]

### Files Analyzed

[Key files examined]
```

## Analysis Techniques

### Framework Detection

**Python Projects:**

```bash
# Check imports
grep -rh "^import \|^from " --include="*.py" . | \
  cut -d' ' -f2 | cut -d'.' -f1 | sort -u | head -20

# Check dependencies
cat requirements*.txt setup.py pyproject.toml 2>/dev/null | \
  grep -E "^[a-zA-Z]" | cut -d'=' -f1 | sort -u
```

**Key frameworks to look for:**
- `textual`, `rich` - TUI frameworks
- `django`, `flask`, `fastapi` - Web frameworks
- `pytest`, `unittest` - Testing
- `sqlalchemy`, `django.db` - ORMs
- `pydantic` - Validation
- `click`, `typer` - CLI frameworks

### Tool Detection

**Look for config files:**

```bash
# Git hooks
ls -la .git/hooks/
cat hk.pkl .pre-commit-config.yaml 2>/dev/null

# Linters/formatters
ls -la .{black,ruff,pylint,mypy,eslint,prettier}* 2>/dev/null

# CI/CD
cat .github/workflows/*.yml .gitlab-ci.yml 2>/dev/null

# Container tools
ls -la Dockerfile* docker-compose*.yml 2>/dev/null
```

### Pattern Mining

**Identify repeated structures:**

```bash
# Find similar class definitions
grep -rh "^class " --include="*.py" . | \
  awk '{print $2}' | sort | uniq -c | sort -rn | head -10

# Find common imports
grep -rh "^from textual" --include="*.py" . | \
  sort | uniq -c | sort -rn | head -10

# Find repeated decorators
grep -rh "^@" --include="*.py" . | \
  sort | uniq -c | sort -rn | head -10
```

### Convention Discovery

**File organization:**
```bash
# Directory structure patterns
find . -type d -maxdepth 3 | head -20

# Naming conventions
find . -name "*.py" -o -name "*.js" | \
  xargs basename -a | head -20
```

**Test patterns:**
```bash
# Test file structure
find . -name "test_*.py" -o -name "*_test.py"

# Test imports
grep -rh "^import pytest\|^from pytest" --include="test_*.py" . | \
  sort | uniq -c
```

## Skill Opportunity Indicators

### Strong Indicators

These suggest a skill is highly valuable:

**1. Repeated Questions**
- Same topics come up frequently
- Multiple team members ask similar questions
- Questions require lengthy explanations

**2. Complex Configuration**
- Tool requires significant setup
- Many configuration options
- Easy to misconfigure

**3. Framework Depth**
- Framework has extensive API surface
- Multiple ways to accomplish tasks
- Best practices not obvious

**4. Pattern Proliferation**
- Same pattern repeated across codebase
- Variations of pattern exist
- Pattern needs consistent application

**5. Tribal Knowledge**
- Knowledge exists only in team members' heads
- Not documented anywhere
- Hard to onboard new contributors

### Weak Indicators

These suggest a skill may not be necessary:

**1. Simple Usage**
- Library used in straightforward way
- Few configuration options
- Self-documenting API

**2. Infrequent Use**
- Used rarely
- Not critical path
- Easy to look up when needed

**3. Well-Documented Externally**
- Excellent official docs
- Many tutorials available
- Active community

**4. One-Time Setup**
- Configure once and forget
- No ongoing decisions
- Rarely modified

## Analysis Workflow

### Step 1: Automatic Detection

Run automated analysis:

```bash
# Create analysis script
cat > analyze_skills.sh <<'EOF'
#!/bin/bash

echo "=== Project Analysis ==="
echo ""

echo "## Frameworks"
if [ -f pyproject.toml ]; then
  echo "Dependencies:"
  grep -E "^\[tool\.|dependencies" pyproject.toml -A 20
fi

echo ""
echo "## Tools"
ls -la .* 2>/dev/null | grep -E "(config|rc|yaml)"

echo ""
echo "## Patterns"
echo "Top imported modules:"
grep -rh "^from \|^import " --include="*.py" . 2>/dev/null | \
  awk '{print $2}' | cut -d'.' -f1 | sort | uniq -c | sort -rn | head -10

EOF

chmod +x analyze_skills.sh
./analyze_skills.sh
```

### Step 2: Manual Review

Examine:
- README.md and documentation
- Recent commit messages
- Issue tracker topics
- Code review comments
- Team discussions

### Step 3: Prioritization

Score potential skills:

**Impact (1-5):**
- How much would this skill help?
- How often would it be used?

**Effort (1-5):**
- How complex is the topic?
- How much content is needed?

**Priority Score = Impact / Effort**

Create high-score skills first.

### Step 4: Validation

Before creating a skill:

1. **Check existing coverage**: Does another skill overlap?
2. **Verify need**: Ask team members if this would be valuable
3. **Test scope**: Is it too broad or too narrow?
4. **Plan structure**: Sketch out main sections

## Example Analyses

### Example 1: TUI Application

**Project Characteristics:**
- Uses Textual framework
- Custom widgets throughout
- Async/await patterns
- Testing with pytest

**Recommended Skills:**
1. ✅ **textual** (HIGH) - Primary framework, complex API
2. ✅ **hk** (HIGH) - Git hooks for code quality
3. 🟡 **pytest-patterns** (MEDIUM) - Testing conventions
4. 🟡 **async-patterns** (MEDIUM) - If complex async logic
5. ⚪ **vcr-cassettes** (LOW) - If domain-specific patterns emerge

### Example 2: Web API

**Project Characteristics:**
- FastAPI framework
- PostgreSQL with SQLAlchemy
- Pydantic models
- Docker deployment

**Recommended Skills:**
1. ✅ **fastapi-patterns** (HIGH) - Core framework
2. ✅ **sqlalchemy** (HIGH) - Complex ORM patterns
3. 🟡 **pydantic-models** (MEDIUM) - Data validation
4. 🟡 **api-conventions** (MEDIUM) - Project-specific patterns
5. ⚪ **docker-compose** (LOW) - Deployment details

### Example 3: Data Pipeline

**Project Characteristics:**
- Pandas data processing
- Custom transformation functions
- Scheduled jobs
- Data quality checks

**Recommended Skills:**
1. ✅ **pipeline-patterns** (HIGH) - Project-specific logic
2. 🟡 **pandas-recipes** (MEDIUM) - Common transformations
3. 🟡 **data-quality** (MEDIUM) - Validation patterns
4. ⚪ **scheduling** (LOW) - Standard cron/scheduler

## Integration with Skill Manager

After analysis, use the skill-manager skill to:

1. Create prioritized skills
2. Structure content appropriately
3. Implement and validate
4. Maintain over time

**Workflow:**
```
skill-analyzer          →  skill-manager
  (identify needs)         (create/update skills)
```

## Reporting Formats

### Quick Audit

For rapid assessment:

```
Current Skills: 2
Missing High-Priority: 2
  - pytest-patterns (testing conventions)
  - async-patterns (async/await guidance)
Missing Medium-Priority: 1
  - project-conventions (file organization)

Next Action: Create pytest-patterns skill
```

### Comprehensive Report

For thorough analysis, use the full report template above with:
- Executive summary
- Detailed recommendations
- Pattern analysis
- Prioritized roadmap

## Best Practices

### When Analyzing

**Do:**
- ✅ Examine actual code usage, not just dependencies
- ✅ Consider team pain points
- ✅ Look for repeated patterns
- ✅ Check for tribal knowledge
- ✅ Validate with team members

**Don't:**
- ❌ Recommend skills for every dependency
- ❌ Create skills for well-documented tools
- ❌ Ignore existing documentation
- ❌ Over-analyze simple projects
- ❌ Create skills no one will use

### Analysis Frequency

**Initial Setup:**
- Comprehensive analysis when starting Claude Skills

**Regular Reviews:**
- Quick audit monthly
- Full analysis quarterly
- After major dependency changes
- When new team members join

**Triggered Reviews:**
- New framework adopted
- Repeated questions on same topic
- Team requests skill for specific area

## Troubleshooting

### No Clear Skill Needs

**Problem:** Project seems too simple or too unique

**Solutions:**
- Focus on project conventions skill
- Document team patterns
- Create testing/quality skills
- Consider meta-skills (like skill-manager)

### Too Many Potential Skills

**Problem:** Everything seems like it needs a skill

**Solutions:**
- Prioritize by impact/effort
- Start with top 2-3
- Create comprehensive skills that cover multiple tools
- Focus on what's unique to your project

### Uncertain Value

**Problem:** Unclear if skill would be helpful

**Solutions:**
- Ask team members
- Try creating minimal version
- Test with actual questions
- Iterate based on usage

## Instructions for Using This Skill

When helping users analyze their project:

1. **Start with discovery**: Run automated detection scripts
2. **Examine patterns**: Look for repeated code structures
3. **Identify gaps**: Compare needs vs. existing skills
4. **Prioritize**: Use impact/effort framework
5. **Recommend**: Provide clear, actionable suggestions
6. **Create report**: Document findings and next steps

Always consider:
- What would provide most value?
- What does the team struggle with?
- What knowledge is undocumented?
- What's the right level of granularity?

## Additional Resources

Related skills:
- **skill-manager**: Creating and maintaining skills
- **skill-sync**: Sharing skills across tools

## Version Notes

This skill reflects Claude Skills as of January 2025. Analysis techniques may evolve with framework and tooling changes.
