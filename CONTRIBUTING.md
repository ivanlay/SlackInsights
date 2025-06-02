# Contributing to SlackInsights

We love your input! We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## We Develop with Github
We use github to host code, to track issues and feature requests, as well as accept pull requests.

## We Use [Github Flow](https://guides.github.com/introduction/flow/index.html)
Pull requests are the best way to propose changes to the codebase. We actively welcome your pull requests:

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code follows the existing style.
6. Issue that pull request!

## Any contributions you make will be under the MIT Software License
In short, when you submit code changes, your submissions are understood to be under the same [MIT License](LICENSE) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using Github's [issues](https://github.com/ivanlay/slackinsights/issues)
We use GitHub issues to track public bugs. Report a bug by [opening a new issue](https://github.com/ivanlay/slackinsights/issues/new); it's that easy!

## Write bug reports with detail, background, and sample code

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

## Development Process

1. **Setup Development Environment**
   ```bash
   git clone https://github.com/ivanlay/slackinsights.git
   cd slackinsights
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your test credentials
   ```

2. **Make Your Changes**
   - Create a new branch: `git checkout -b feature/your-feature-name`
   - Make your changes
   - Add tests if applicable
   - Run the bot locally to test: `python slack_summary_bot.py`

3. **Code Style**
   - Use 4 spaces for indentation (not tabs)
   - Follow PEP 8 style guide
   - Use meaningful variable and function names
   - Add docstrings to all functions
   - Keep functions focused and small

4. **Testing**
   - Test with different Slack channel configurations
   - Verify error handling works correctly
   - Check that summaries are generated properly
   - Test with various message types (threads, mentions, etc.)

5. **Commit Your Changes**
   - Use clear and meaningful commit messages
   - Reference any related issues

6. **Submit a Pull Request**
   - Push your branch to your fork
   - Open a PR against the main repository
   - Describe your changes and why they're needed
   - Link any relevant issues

## Feature Requests

We love feature requests! When submitting a feature request:

1. **Check existing issues** first to avoid duplicates
2. **Provide context**: Why is this feature important?
3. **Be specific**: What exactly should the feature do?
4. **Consider implementation**: Any thoughts on how it might work?

## Code Review Process

The maintainers will review your PR and may:
- Request changes
- Ask questions
- Suggest improvements
- Merge your PR when it's ready

We aim to review PRs within a week.

## Community

- Be respectful and inclusive
- Help others when you can
- Share your knowledge
- Celebrate contributions of all sizes

## Questions?

Feel free to open an issue with your question or reach out to the maintainers.

Thank you for contributing! 🎉