# Glacium Development Guidelines

These rules apply to all files in this repository.

## Code Style

- Use **black** (default settings) for formatting.  The CI uses the same configuration.
- Write type hints for all new Python functions and methods.
- Keep imports sorted with **isort**.

## Testing

- Set up the development environment once with:

  ```bash
  poetry install --with dev
  poetry self add "poetry-dynamic-versioning[plugin]"
  ```

- Run the test suite with `pytest` before committing.

## Documentation

- Build the Sphinx documentation via `make -C docs html` to ensure that no warnings are introduced.

## Commit Messages

- Start commit messages with a short, uppercase tag such as `FEAT`, `FIX`, or `DOC`.
- Follow the tag with a short summary in the same line.

