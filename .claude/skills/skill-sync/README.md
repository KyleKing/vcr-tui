# Skill Sync

Syncs Claude Skills with other AI coding tools (Cursor, GitHub Copilot, Continue.dev, etc.) to create unified knowledge bases.

## Purpose

This meta-skill provides expertise in:
- Creating .cursorrules files that reference skills
- Integrating skills with multiple AI tools
- Maintaining consistency across assistants
- Generating tool-specific configs from skills
- Automating cross-tool synchronization

## When to Use

Ask Claude to use this skill when you:
- Want to use skills with Cursor or other AI tools
- Need to create a .cursorrules file
- Want unified AI context across tools
- Need to sync skills with team tools
- Want to automate config generation

## Key Features

### Cross-Tool Integration
- Cursor (.cursorrules)
- GitHub Copilot (context docs)
- Continue.dev (config.json)
- Codeium (documentation)
- Other AI coding assistants

### Sync Strategies
- **Reference-based**: Point to skills (recommended)
- **Summary-based**: Condensed versions
- **Shared docs**: Central documentation

### Automation
- Scripts to generate configs
- Git hooks for auto-sync
- Version tracking
- Consistency checking

## Quick Start

**Create .cursorrules:**
```
User: "Create a .cursorrules file that references my skills"
Claude: [Uses skill-sync to generate appropriate config]
```

**Sync with multiple tools:**
```
User: "How do I share these skills with Cursor and Copilot?"
Claude: [Provides tool-specific integration strategies]
```

## File Organization

```
project/
├── .cursorrules              # Cursor AI context
├── .claude/skills/           # Primary knowledge base
├── docs/COPILOT_CONTEXT.md  # Copilot context
└── README.md                 # References guidance
```

## Best Practices

- Keep `.claude/skills/` as source of truth
- Use references over duplication
- Maintain consistent terminology
- Test guidance across tools
- Automate sync when possible

## Related Skills

- **skill-manager**: Maintains the skills being synced
- **skill-analyzer**: Identifies skills to sync

## Files

- `SKILL.md`: Main skill definition with sync strategies
