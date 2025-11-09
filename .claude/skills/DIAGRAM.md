# Claude Skills System Architecture

Visual representation of the skills system and how components interact.

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        User Question                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     Claude Code                              │
│  - Analyzes query                                            │
│  - Matches skill triggers                                    │
│  - Loads relevant skill(s)                                   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              .claude/skills/ (Knowledge Base)                │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   textual    │  │      hk      │  │skill-manager │      │
│  │  Framework   │  │  Git Hooks   │  │  Lifecycle   │      │
│  │   Guidance   │  │  Management  │  │  Management  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │skill-analyzer│  │  skill-sync  │                        │
│  │   Project    │  │  Cross-Tool  │                        │
│  │   Analysis   │  │  Integration │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Expert Guidance                           │
│  - Code examples                                             │
│  - Best practices                                            │
│  - Common pitfalls                                           │
│  - Framework patterns                                        │
└─────────────────────────────────────────────────────────────┘
```

## Cross-Tool Integration

```
┌─────────────────────────────────────────────────────────────┐
│            .claude/skills/ (Source of Truth)                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          │ (References, not duplication)
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ .cursorrules │  │docs/         │  │.continue/    │
│              │  │COPILOT_      │  │config.json   │
│   Cursor     │  │CONTEXT.md    │  │              │
│   Context    │  │              │  │ Continue.dev │
│              │  │GitHub Copilot│  │   Context    │
└──────────────┘  └──────────────┘  └──────────────┘
```

## Meta-Skills Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Analyze Project                                      │
│                                                              │
│  User: "What skills should I create?"                        │
│                                                              │
│  ┌──────────────────┐                                       │
│  │ skill-analyzer   │                                       │
│  │                  │                                       │
│  │ • Scans codebase │                                       │
│  │ • Detects tools  │                                       │
│  │ • Finds patterns │                                       │
│  │ • Recommends     │                                       │
│  └────────┬─────────┘                                       │
└───────────┼─────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Create/Update Skills                                 │
│                                                              │
│  User: "Create skill for pytest patterns"                   │
│                                                              │
│  ┌──────────────────┐                                       │
│  │ skill-manager    │                                       │
│  │                  │                                       │
│  │ • Creates SKILL  │                                       │
│  │ • Structures     │                                       │
│  │ • Validates      │                                       │
│  │ • Maintains      │                                       │
│  └────────┬─────────┘                                       │
└───────────┼─────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Sync Across Tools                                    │
│                                                              │
│  User: "Share skills with Cursor"                           │
│                                                              │
│  ┌──────────────────┐                                       │
│  │ skill-sync       │                                       │
│  │                  │                                       │
│  │ • Generates      │                                       │
│  │   .cursorrules   │                                       │
│  │ • References     │                                       │
│  │   skills         │                                       │
│  │ • Maintains sync │                                       │
│  └──────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘
```

## Skill Structure

```
skill-name/
│
├── SKILL.md                    ← Main skill (REQUIRED)
│   ├── Frontmatter (name, description)
│   ├── Core concepts
│   ├── Common patterns
│   ├── Best practices
│   └── Instructions
│
├── README.md                   ← Documentation
│   ├── Purpose
│   ├── When to use
│   └── Quick examples
│
├── quick-reference.md          ← Fast lookups
│   ├── Cheat sheets
│   ├── Templates
│   └── Commands
│
├── guide.md                    ← Deep dive
│   ├── Architecture
│   ├── Advanced topics
│   └── Detailed examples
│
└── examples.md                 ← Code samples
    ├── Use cases
    └── Complete examples
```

## Information Flow

```
Developer Workflow:

┌──────────────┐
│ Write Code   │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌─────────────────┐
│ Ask Question ├────→│ Claude Code     │
└──────────────┘     │ + Skills        │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │ Expert Guidance │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │ Better Code     │
                     └─────────────────┘

Alternative Workflow (Cursor):

┌──────────────┐
│ Write Code   │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌─────────────────┐
│ Ask Cursor   ├────→│ .cursorrules    │
└──────────────┘     │ references      │
                     │ skills          │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │ Cursor reads    │
                     │ .claude/skills/ │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │ Consistent      │
                     │ Guidance        │
                     └─────────────────┘
```

## Skill Invocation

```
Query: "How do I create a Textual widget?"
                     │
                     ▼
         ┌───────────────────────┐
         │ Keyword Matching      │
         │                       │
         │ Checks descriptions:  │
         │ - "textual"           │
         │ - "widget"            │
         │ - "TUI"               │
         └───────────┬───────────┘
                     │
                     ▼ (Match found!)
         ┌───────────────────────┐
         │ Load textual skill    │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │ Access resources:     │
         │ - SKILL.md            │
         │ - quick-reference.md  │
         │ - guide.md            │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │ Provide guidance:     │
         │ - Code example        │
         │ - Best practices      │
         │ - Common pitfalls     │
         └───────────────────────┘
```

## Maintenance Cycle

```
          ┌─────────────────────┐
          │   Regular Review    │
          │                     │
          │ • Monthly: Check    │
          │   for outdated info │
          │ • Quarterly: Major  │
          │   framework updates │
          └──────────┬──────────┘
                     │
                     ▼
          ┌─────────────────────┐
          │ skill-analyzer      │
          │                     │
          │ Identify gaps:      │
          │ • New frameworks    │
          │ • Missing patterns  │
          │ • Outdated content  │
          └──────────┬──────────┘
                     │
                     ▼
          ┌─────────────────────┐
          │ skill-manager       │
          │                     │
          │ Update skills:      │
          │ • Modify content    │
          │ • Add patterns      │
          │ • Update examples   │
          └──────────┬──────────┘
                     │
                     ▼
          ┌─────────────────────┐
          │ skill-sync          │
          │                     │
          │ Sync changes:       │
          │ • Update .cursor    │
          │ • Sync docs         │
          │ • Test integration  │
          └──────────┬──────────┘
                     │
                     ▼
          ┌─────────────────────┐
          │   Updated System    │
          └─────────────────────┘
                     │
                     └──────────┐
                                │
          (Loop back to review) │
                                │
          ┌─────────────────────┘
          │
          ▼
    (Continue cycle...)
```

## File Dependencies

```
Project Root
│
├── .cursorrules ──────────┐
│                          │
├── .claude/               │
│   └── skills/            │
│       ├── README.md      │ (References)
│       │                  │
│       ├── textual/  ◄────┤
│       │   ├── SKILL.md   │
│       │   ├── quick-reference.md
│       │   ├── guide.md   │
│       │   └── README.md  │
│       │                  │
│       ├── hk/  ◄─────────┤
│       │   ├── SKILL.md   │
│       │   ├── reference.md
│       │   └── examples.md
│       │                  │
│       ├── skill-manager/ │
│       ├── skill-analyzer/ 
│       └── skill-sync/ ◄──┘
│
└── docs/  (Optional)
    └── COPILOT_CONTEXT.md ──→ References .claude/skills/
```

## Legend

```
┌─────────┐
│ Process │   Rectangle with text
└─────────┘

    │
    ▼         Directional flow
    
───→          Reference/link

◄───           Bidirectional reference

┬ ┼ ┴ ├ ┤     Connection points
```

---

This diagram provides a visual overview of how Claude Skills work together
to create a self-improving, cross-tool knowledge management system.
