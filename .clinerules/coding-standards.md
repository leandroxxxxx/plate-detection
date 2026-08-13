# Coding Standards

## Language: English only

This project is always written in English. This applies to everything persisted in the codebase:

- Code identifiers: variables, functions, classes, modules, packages.
- Comments and docstrings.
- Error messages and log messages.
- File and directory names.
- Commit messages and project documentation (README, docs, etc.).

Portuguese is allowed only in the conversation with the user. Never write Portuguese in files, code, commits, or documentation of this project.

## File size: continuous evaluation

Always assess the size of every file before delivering work.

- Code files above ~200 lines should be split into smaller files, separating responsibilities (Single Responsibility Principle).
- This is a guideline, not a hard rule: evaluate case by case. A long, cohesive module may be acceptable, but the split must be considered whenever a file exceeds this limit.
- When splitting, extract cohesive responsibilities into their own modules, keeping imports and organization clean.