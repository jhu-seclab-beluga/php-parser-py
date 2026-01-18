---
description: Code quality standards and best practices for programming tasks
---

# Code Quality Standards

## Control Flow Optimization
- Prefer early returns over nested conditionals
- Use guard clauses to minimize nesting
- Use `continue`/`break` instead of nested `if` blocks
- Keep logic flat, max 3 nesting levels

## Error Handling
- Catch specific exception types (avoid broad `except Exception`)
- Handle errors at appropriate abstraction level
- Preserve exception context with `from e`
- Provide meaningful error messages
- **Avoid silent fallback mechanisms**: Raise exceptions instead of silently falling back to alternative implementations
- **Fail fast**: Raise exceptions immediately on initialization/operation failure, do not silently degrade functionality
- **Exception-driven**: Use exceptions to communicate errors clearly, avoid hiding errors through fallback
- **Never silent fallback**: Never silently return empty values (empty strings, empty lists, None) when operations fail. Always log errors at appropriate level (ERROR for critical failures, WARNING for recoverable issues) and either raise exceptions or provide clear error messages in logs

## Code Structure
- Keep functions short (ideally < 20 lines)
- Extract complex logic into dedicated functions
- Avoid deep nesting (max 3 levels)
- Use meaningful variable and function names

## Performance
- Use context managers for resource management/cleanup
- Avoid unnecessary object creation in loops
- Check caches before expensive operations
- Optimize critical paths

## Documentation
- Use English for comments and docs
- Explain why (rationale) rather than what
- Add type hints to all function parameters and return values
- Prefer specific types over generic ones
- **No historical notes**: Do not include comments about code evolution or previous implementations
- **No iteration history**: Remove comments about previous design decisions that are no longer relevant

### Func or Class Document Standards
- Detail document only public API (no leading underscore). Private methods use a brief single-line comment to summarize the usage
- For functions/classes in design documents, docstrings must include all information from the corresponding design document section
- Write for developers using the code: one sentence summary, important constraints/assumptions/side effects, parameter descriptions, return value description, exceptions raised
- Be concise: no redundancy, no implementation details, no examples (examples belong in separate docs/tests)
- Use structured Google-style format:
  - **Functions**: one sentence summary, followed by `Args:` section listing each parameter with description, `Returns:` section describing return value, and `Raises:` section listing exceptions when applicable
  - **Classes**: one sentence summary, followed by `Attributes:` section listing public attributes when applicable, and additional sections for important constraints/assumptions/side effects

## Testing
- Prefer one assertion per test when practical
- Use descriptive test names (scenario + expectation)
- Follow Arrange–Act–Assert pattern
- Keep tests focused and isolated, use fixtures for common setup
- Cover positive and negative paths, assert error conditions explicitly

## API Design
- Use core module APIs directly
- Avoid direct dependencies on infrastructure services
- Prefer exception-driven error handling
- Build self-contained modules
- Keep data containers passive, avoid embedding behavior in simple data models
- Represent application logic as explicit callables/functions

## Code Quality Workflow
### Pre-Modification
- Run quality tools on target files
- Check score and identify issues
- Review warnings before making changes

### During Development
- Follow control flow optimization guidelines
- Follow naming conventions and code structure rules
- Add type hints and documentation
- Use context managers for resource management
- Use appropriate design patterns

### Post-Modification
- Run quality tools again
- Target score: 9.0+ for all modules
- Fix all warnings before proceeding
- Apply formatting and import organization tools
- Verify structure follows standards

### Phase Completion Gate
- Run comprehensive quality checks
- Verify all files formatted consistently
- Run all unit tests
- Verify test coverage and quality
- Verify no critical issues remain
- All gates must pass before proceeding

## Logging Standards
- Use Python standard `logging` module
- Get logger: `logger = logging.getLogger(__name__)` at module level
- Use lazy % formatting: `logger.info("Message: %s", var)` not f-strings
- **Add logs only when necessary**: each log must serve a clear debugging or monitoring purpose
- **No redundant logs**: avoid duplicate messages across modules for the same event
- **No trivial logs**: skip logging for simple operations (getters, setters, straightforward flows)
- **Never silent failures**: when operations fail and return fallback values (empty strings, None, empty lists), always log the failure with appropriate level (ERROR for critical failures, WARNING for recoverable issues)
- Log levels:
  - DEBUG: complex logic diagnostics, non-obvious implementation details
  - INFO: key business results, flow milestones only (use sparingly)
  - WARNING: recoverable issues, unexpected but handled conditions, fallback operations
  - ERROR: failures requiring attention, critical operation failures
- **Layer appropriately**: high-level modules use INFO for results; low-level modules use DEBUG
- Include context in message string using % formatting
- Use `logger.exception()` for exceptions (auto-includes traceback)
- Avoid logging sensitive information (API keys, passwords, personal data)
- Example:
  ```python
  import logging
  logger = logging.getLogger(__name__)
  logger.debug("Processing item: %s", item_id)
  logger.info("Completed: %d items in %.2f seconds", count, duration)
  logger.warning("Low confidence: %.2f for %s", confidence, var_name)
  logger.error("Failed: %s", error_message)
  logger.exception("Unexpected error occurred")
  ```