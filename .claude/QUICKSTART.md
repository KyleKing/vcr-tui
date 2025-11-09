# Claude Skills Quick Start

Welcome to your project's Claude Skills system! This guide will get you started in 5 minutes.

## What You Have

Your project now has a **self-managing, cross-tool AI knowledge base** with:

- ✅ 5 specialized skills (2 framework + 3 meta-skills)
- ✅ ~172 KB of structured guidance
- ✅ Automatic invocation based on context
- ✅ Cross-tool integration (Cursor, Copilot, etc.)

## 🎯 Try It Now

### Test #1: Framework Guidance

Ask Claude:
```
"How do I create a Textual widget with reactive state?"
```

**Expected:** The `textual` skill activates and provides:
- Code example with reactive attributes
- Best practices
- Common pitfalls to avoid

### Test #2: Skill Management

Ask Claude:
```
"What skills should I create for this project?"
```

**Expected:** The `skill-analyzer` skill:
- Scans your codebase
- Identifies frameworks and tools
- Recommends prioritized skills

### Test #3: Cross-Tool Sync

Ask Claude:
```
"Explain the .cursorrules file"
```

**Expected:** The `skill-sync` skill explains:
- How .cursorrules references skills
- Cross-tool integration strategy
- How to maintain sync

## 📚 Documentation Map

**Quick Reference:**
- 📖 This file: Quick start
- 📋 `skills/README.md`: Complete guide
- 📐 `skills/DIAGRAM.md`: Visual architecture
- 📊 `../SKILLS_SUMMARY.md`: Implementation details

**Framework Skills:**
- 🎨 `skills/textual/`: Textual TUI framework
- 🪝 `skills/hk/`: Git hook management

**Meta-Skills:**
- 🛠️ `skills/skill-manager/`: Create/update skills
- 📊 `skills/skill-analyzer/`: Find skill gaps
- 🔄 `skills/skill-sync/`: Share across tools

**Tool Integration:**
- 📝 `../.cursorrules`: Cursor AI context

## 🚀 Common Tasks

### View All Skills

```
Ask: "What skills exist in this project?"
```

### Get Framework Help

```
Ask: "How do I [Textual/hk task]?"
```

### Create a New Skill

```
1. Ask: "What skills should I create?"
2. Ask: "Create a skill for [topic]"
3. Test: Ask a question that should trigger it
```

### Update Existing Skill

```
Ask: "Update the [skill-name] skill with [changes]"
```

### Share with Other Tools

```
Ask: "How do I use these skills with Cursor?"
```

## 🎓 Learn More

### Understand Skills

Read: `.claude/skills/README.md`

Key concepts:
- How skills are triggered
- File structure
- Best practices

### Manage Skills

Read: `.claude/skills/skill-manager/SKILL.md`

Learn to:
- Create skills from scratch
- Update with new information
- Maintain quality

### Analyze Needs

Read: `.claude/skills/skill-analyzer/SKILL.md`

Learn to:
- Detect project requirements
- Prioritize skill creation
- Identify gaps

### Cross-Tool Integration

Read: `.claude/skills/skill-sync/SKILL.md`

Learn to:
- Share with Cursor
- Configure Copilot
- Maintain consistency

## 💡 Pro Tips

**1. Skills trigger automatically**
   Just ask naturally - Claude finds the right skill

**2. Reference supporting files**
   Each skill has quick-reference.md and guide.md for depth

**3. Meta-skills work together**
   analyzer → manager → sync creates a complete workflow

**4. Keep .cursorrules synchronized**
   When skills change, update .cursorrules references

**5. Create project-specific skills**
   Document your unique patterns and conventions

## 🐛 Troubleshooting

### Skill Not Triggering?

**Check:**
1. Use keywords from skill description
2. Ask more specific questions
3. View skill description: `head .claude/skills/[name]/SKILL.md`

### Need Different Guidance?

**Options:**
1. Update existing skill
2. Create new skill for specific need
3. Use skill-analyzer to identify gaps

### Cross-Tool Not Working?

**Verify:**
1. `.cursorrules` exists in project root
2. File references correct skill paths
3. Other tool supports context files

## 📈 Next Steps

### Week 1: Familiarize
- [ ] Test all existing skills
- [ ] Read main documentation
- [ ] Try creating a simple skill

### Week 2: Customize
- [ ] Run skill-analyzer
- [ ] Create project-specific skills
- [ ] Update .cursorrules

### Week 3: Integrate
- [ ] Share with team
- [ ] Configure other tools (Cursor, etc.)
- [ ] Gather feedback

### Ongoing: Maintain
- [ ] Review skills monthly
- [ ] Update with new patterns
- [ ] Expand coverage as needed

## 🤝 Getting Help

**Within this project:**

Ask Claude:
- "How do I use skill-manager?"
- "Explain skill-analyzer"
- "Help with skill-sync"

**External resources:**

- Claude Code docs: https://docs.claude.com/claude-code
- Textual docs: https://textual.textualize.io
- hk documentation: https://github.com/jdx/hk

## ✨ Quick Wins

**Immediate value:**

1. **Consistent guidance** - Same answers every time
2. **Faster development** - Patterns at your fingertips
3. **Better onboarding** - New team members get instant help
4. **Cross-tool knowledge** - Use skills in Cursor too

**Long-term benefits:**

1. **Self-documenting** - Knowledge captured as you go
2. **Scalable** - Grows with your project
3. **Maintainable** - Easy to update
4. **Shareable** - Team benefits together

---

**Ready to start? Just ask Claude a question!**

Try: _"How do I create a Textual widget?"_

---

**Last Updated:** 2025-01-09
**Skills Version:** 1.0
**For detailed information:** See `.claude/skills/README.md`
