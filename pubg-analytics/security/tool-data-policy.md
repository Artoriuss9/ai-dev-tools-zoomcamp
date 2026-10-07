# AI tool and data policy

- Never provide `.env` contents, API keys, bearer tokens, or deployment
  credentials to an AI tool.
- Use synthetic nicknames and match fixtures when asking for code or test help.
- Do not submit real player records, private user data, database files, or
  production logs to external services.
- Review AI-generated code, dependencies, commands, and configuration before
  running or merging them.
- Do not execute destructive commands suggested by a tool without confirming
  their exact scope and impact.
- Use least-privilege, read-only access by default. Deployment credentials, if
  added, belong only in protected CI secrets and must never be exposed to
  pull-request builds from forks.
- Treat AI output as untrusted until tests, static analysis, and manual review
  support it.
