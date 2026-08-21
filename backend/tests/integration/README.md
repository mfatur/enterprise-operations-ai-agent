# Optional integration tests

Integration tests are intentionally opt-in. The normal deterministic test
command does not run tests marked `integration`:

```powershell
python -m pytest -q
```

PostgreSQL integration tests require `SALES_AGENT_TEST_DATABASE_URL`. It must
point to a dedicated test database; `DATABASE_URL` is intentionally never used
as a fallback. For an additional safety check, the target database name must
include `test`.

Set the value only in the process environment, without committing or printing
credentials. For example, replace the placeholder locally with a dedicated
test-database URL:

```powershell
$env:SALES_AGENT_TEST_DATABASE_URL = "<dedicated test database URL>"
python -m pytest -m database
```

The PostgreSQL tests create a unique schema for each test, set the connection
search path only for the test session, and drop that schema afterward. They do
not create or delete databases and do not modify `public.orders`.

Gemini integration tests require explicit Gemini credentials. They can
use the network and may incur latency, quota usage, or API cost. Keep them
separate from the normal test suite and run them only when those effects are
intended.

The Gemini smoke test is opt-in and requires `GEMINI_API_KEY` through the
application's existing configuration. Never commit `.env`, print the API key,
or include it in test output. The test makes one graph invocation, does not
modify database data, and checks that the final response has useful text; it
does not assert exact Gemini wording.

Once integration tests are implemented and appropriately marked, select them
explicitly with one of these commands:

```powershell
python -m pytest -m integration
python -m pytest -m database
python -m pytest -m gemini
```

Run the Gemini smoke test only intentionally:

```powershell
python -m pytest -m gemini -q
```

Gemini API usage may consume quota or incur cost. PostgreSQL integration tests
skip cleanly unless `SALES_AGENT_TEST_DATABASE_URL` is explicitly set.
