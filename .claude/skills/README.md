# Claude Skills - Project Knowledge Base

This directory contains **Claude Skills** - specialized knowledge modules that provide expert guidance for development.

## What are Claude Skills?

Claude Skills are domain-specific knowledge bases that:
- Provide expert-level guidance on frameworks, tools, and patterns
- Are automatically invoked by Claude Code when relevant
- Maintain consistent, comprehensive project knowledge
- Enable rapid onboarding and reduce repeated questions
- Can be shared across AI tools (Cursor, Copilot, etc.)

## Skills in This Project

### 🎨 Textual TUI Framework
**Location:** `textual/`

Comprehensive guidance for building terminal user interfaces with Textual:
- Core concepts and architecture
- Widget patterns and composition
- Reactive programming
- CSS (TCSS) styling
- Testing strategies
- Common pitfalls and solutions

**Files:**
- `SKILL.md` - Main skill with triggers and overview
- `quick-reference.md` - Cheat sheets and templates
- `guide.md` - Comprehensive architectural guide
- `README.md` - Skill documentation

**Invoke when:** Building TUI apps, working with widgets, styling, testing Textual code

---

### 🪝 Git Hooks (hk)
**Location:** `hk/`

Git hook management with the hk tool:
- Installation and setup
- Configuration patterns
- Built-in linters
- Pre-commit/pre-push hooks
- Integration with mise

**Files:**
- `SKILL.md` - Main skill definition
- `reference.md` - Detailed configuration reference
- `examples.md` - Configuration examples

**Invoke when:** Setting up git hooks, configuring linters, managing pre-commit checks

---

### 🛠️ Skill Manager (Meta-Skill)
**Location:** `skill-manager/`

Manages the lifecycle of Claude Skills:
- Creating new skills
- Updating existing skills
- Maintaining quality
- Versioning and tracking
- Best practices

**Files:**
- `SKILL.md` - Complete skill management guide
- `README.md` - Quick overview

**Invoke when:** Creating/updating skills, improving skill structure, versioning

---

### 📊 Skill Analyzer (Meta-Skill)
**Location:** `skill-analyzer/`

Analyzes codebases to identify needed skills:
- Framework and tool detection
- Pattern recognition
- Gap analysis
- Prioritized recommendations
- Impact/effort scoring

**Files:**
- `SKILL.md` - Analysis framework and methods
- `README.md` - Quick overview

**Invoke when:** Determining what skills to create, auditing coverage, identifying gaps

---

### 🔄 Skill Sync (Meta-Skill)
**Location:** `skill-sync/`

Syncs skills with other AI coding tools:
- Cursor (.cursorrules)
- GitHub Copilot
- Continue.dev
- Cross-tool integration
- Automated synchronization

**Files:**
- `SKILL.md` - Sync strategies and implementation
- `README.md` - Quick overview

**Invoke when:** Sharing skills with Cursor/Copilot, creating .cursorrules, unified AI context

---

## How Skills Work

### Automatic Invocation

Claude Code automatically loads skills based on the `description` field in each `SKILL.md`:

```yaml
---
name: textual
description: Expert guidance for building TUI applications with Textual.
  Invoke when user asks about Textual, widgets, screens, CSS styling,
  reactive programming, or testing TUI apps.
---
```

When you mention these keywords, Claude loads the skill and provides expert guidance.

### Skill Structure

Each skill follows this structure:

```
skill-name/
├── SKILL.md              # Main definition (REQUIRED)
├── README.md             # Documentation about the skill
├── quick-reference.md    # Quick lookups (optional)
├── guide.md              # Detailed explanations (optional)
└── examples.md           # Code examples (optional)
```

**SKILL.md** is the only required file. Others add depth and quick reference material.

### Supporting Files

Skills can reference supporting documentation:

```markdown
For detailed examples, see [examples.md](examples.md).
For quick lookups, see [quick-reference.md](quick-reference.md).
```

## Using Skills

### As a Developer

Just ask Claude naturally:

```
"How do I create a Textual widget?"
→ Loads textual skill, provides guidance

"How do I set up git hooks with hk?"
→ Loads hk skill, explains setup

"What skills should I create for this project?"
→ Loads skill-analyzer, examines codebase
```

### With Other AI Tools

Skills can be shared with Cursor, GitHub Copilot, and other AI assistants.

**See:** `.cursorrules` in project root for Cursor integration.

**Learn more:** `skill-sync/SKILL.md` for cross-tool strategies.

## Creating New Skills

### Quick Start

1. **Identify the need** (or use skill-analyzer)
   ```
   "What skills should I create for this project?"
   ```

2. **Create the skill** (use skill-manager)
   ```
   "Create a skill for pytest testing patterns"
   ```

3. **Test invocation**
   ```
   "How do I write a pytest fixture?"
   (Verify skill is invoked)
   ```

### Manual Creation

```bash
# 1. Create directory
mkdir -p .claude/skills/new-skill

# 2. Create SKILL.md with frontmatter
cat > .claude/skills/new-skill/SKILL.md << 'EOF'
---
name: new-skill
description: Clear description with trigger keywords
---

# Skill Name

[Content...]
EOF

# 3. Test
# Ask Claude a question that should trigger the skill
```

**For detailed guidance:** See `skill-manager/SKILL.md`

## Maintaining Skills

### Regular Updates

- **Monthly**: Review for outdated information
- **Quarterly**: Update with new framework versions
- **As needed**: Add new patterns discovered

### Version Tracking

Add version history to README.md:

```markdown
## Version History

### v2.0 - 2025-01-09
- Updated for Framework v5.0
- Added new patterns
- Deprecated old approaches
```

### Quality Checklist

- [ ] Clear, specific trigger description
- [ ] Working, tested examples
- [ ] Current best practices
- [ ] No contradictions with other skills
- [ ] Links and references work

**For detailed guidance:** See `skill-manager/SKILL.md`

## Cross-Tool Integration

### Cursor AI

This project includes `.cursorrules` that references skills:

```markdown
# .cursorrules

## Textual Framework
Brief patterns...
Full details: `.claude/skills/textual/`
```

### GitHub Copilot

Copilot learns from:
- Code patterns in the repository
- Comments and docstrings
- README and documentation
- `.cursorrules` (indirectly, via context)

### Continue.dev

Configure to reference skills:

```json
{
  "contextProviders": [{
    "name": "skills",
    "patterns": [".claude/skills/*/SKILL.md"]
  }]
}
```

**For detailed guidance:** See `skill-sync/SKILL.md`

## Best Practices

### Content Guidelines

**Do:**
- ✅ Keep triggers specific and comprehensive
- ✅ Provide working code examples
- ✅ Include common pitfalls
- ✅ Link to official documentation
- ✅ Maintain consistent terminology
- ✅ Test all examples

**Don't:**
- ❌ Copy entire documentation sites
- ❌ Include untested code
- ❌ Make skills too broad
- ❌ Duplicate information
- ❌ Use vague triggers

### Naming Conventions

- **Directories**: `lowercase-with-hyphens`
- **SKILL.md**: Always uppercase
- **README.md**: Uppercase
- **Other files**: `lowercase-with-hyphens.md`

### File Organization

```
.claude/skills/
├── README.md                    # This file
├── framework-name/              # Framework skills
│   ├── SKILL.md
│   ├── quick-reference.md
│   └── guide.md
├── tool-name/                   # Tool skills
│   ├── SKILL.md
│   └── reference.md
├── project-patterns/            # Project-specific
│   └── SKILL.md
└── meta-skills/                 # Skills about skills
    ├── skill-manager/
    ├── skill-analyzer/
    └── skill-sync/
```

## Troubleshooting

### Skill Not Invoking

**Check:**
1. Frontmatter format correct?
2. Description includes trigger keywords?
3. File named `SKILL.md` (uppercase)?
4. File in `.claude/skills/<name>/` directory?

**Fix:**
```bash
# Verify structure
ls -la .claude/skills/<skill-name>/SKILL.md

# Check frontmatter
head -10 .claude/skills/<skill-name>/SKILL.md
```

### Outdated Content

**Update process:**
1. Edit skill content
2. Update version in README
3. Test examples still work
4. Update `.cursorrules` if needed

**For detailed guidance:** See `skill-manager/SKILL.md`

### Multiple Skills Triggering

**Problem:** Too many skills activate for same query

**Solution:**
- Make descriptions more specific
- Narrow skill scope
- Split broad skills into focused ones

## Meta-Skills Workflow

These skills work together:

```
skill-analyzer              skill-manager              skill-sync
     ↓                            ↓                         ↓
"What skills do            "Create skill for         "Share skills with
 I need?"                   pytest patterns"          Cursor/Copilot"
     ↓                            ↓                         ↓
Examines codebase    →     Creates SKILL.md    →     Generates .cursorrules
Recommends priorities      Structures content         Syncs across tools
```

## Examples

### Example 1: Getting Started

```
User: "What skills exist in this project?"
Claude: [Lists skills from this README]

User: "How do I create a Textual widget?"
Claude: [Loads textual skill, provides patterns]

User: "Show me a complete example"
Claude: [References textual/examples.md]
```

### Example 2: Creating Skills

```
User: "Analyze what skills I should create"
Claude: [Uses skill-analyzer, examines project]

User: "Create a skill for the top recommendation"
Claude: [Uses skill-manager, creates skill]

User: "Share these skills with Cursor"
Claude: [Uses skill-sync, generates .cursorrules]
```

### Example 3: Maintenance

```
User: "Update the textual skill for version 0.50"
Claude: [Uses skill-manager, plans updates]

User: "Are my skills up to date?"
Claude: [Uses skill-analyzer, checks for gaps]
```

## Additional Resources

### Official Documentation

- **Claude Code**: https://docs.claude.com/claude-code
- **Textual**: https://textual.textualize.io
- **hk**: https://github.com/jdx/hk

### Skill Development

- **skill-manager**: Creating and updating skills
- **skill-analyzer**: Identifying needed skills
- **skill-sync**: Cross-tool integration

### Community

- Share your skills with the community
- Learn from others' skill structures
- Contribute improvements

## Quick Reference

| Task | Command/Question |
|------|-----------------|
| List skills | "What skills exist?" |
| Use a skill | "How do I [topic from skill]?" |
| Create skill | "Create a skill for [topic]" |
| Update skill | "Update [skill-name] for [changes]" |
| Analyze needs | "What skills should I create?" |
| Sync tools | "Share skills with Cursor" |

---

**Last Updated:** 2025-01-09
**Skills Version:** 1.0
**Claude Code Version:** January 2025 release

For questions or improvements, see the meta-skills:
- `skill-manager/` - Skill lifecycle
- `skill-analyzer/` - Identifying needs
- `skill-sync/` - Cross-tool sharing
