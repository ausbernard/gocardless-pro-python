# GoCardless Pro Python — Recon

## What It Is

Official Python client library for the [GoCardless Pro API](https://developer.gocardless.com/). GoCardless is a payments infrastructure company specializing in bank-to-bank payments (Direct Debit via SEPA, ACH, Bacs). This library is the Python SDK developers use to integrate GoCardless into their applications.

- **Version:** 3.3.0
- **Python Support:** 3.8, 3.9, 3.10, 3.11, 3.12
- **License:** MIT
- **Status:** Actively maintained, generated via an internal GoCardless tool called "Crank"

---

## High-Level Architecture

```
Client (entry point)
  └── 50+ Services (per resource: customers, payments, mandates, etc.)
        └── ApiClient (HTTP via requests library)
              └── Errors (custom exception hierarchy)
```

| Layer | File(s) | Role |
|---|---|---|
| Entry point | `client.py` | Lazily instantiates all services |
| HTTP | `api_client.py` | Wraps `requests`, handles auth/headers |
| Services | `services/*.py` | CRUD + custom actions per API resource |
| Resources | `resources/*.py` | Thin response wrappers (read-only props) |
| Errors | `errors.py` | 8 specific API error types |
| Pagination | `paginator.py` | Cursor-based auto-pagination |
| Webhooks | `webhooks.py` | HMAC-SHA256 signature verification |
| Rate limiting | `rate_limit.py` | Tracks `X-RateLimit-*` headers |

**Key behaviors:**
- Bearer token auth via `access_token`
- Two environments: `sandbox` and `live`
- Auto-retry on network failures (3 retries, 0.5s delay)
- Auto-injected idempotency keys on POST to prevent duplicates
- Cursor-based pagination with iterator interface

---

## Bugs & Issues Worth Contributing

These are real bugs with clear, bounded fixes. Most are not in generated code (which gets overwritten by Crank), so they are either in hand-written files or documentation.

---

### Bug 1 — Rate limit API: docs say attribute access, code returns a dict

**File:** `gocardless_pro/client.py` lines 226–231  
**Severity:** High — breaks documented usage

The README documents:
```python
client.rate_limit.limit
client.rate_limit.remaining
client.rate_limit.reset
```

But `client.rate_limit` returns a plain `dict`:
```python
return {
    "ratelimit-limit": self._api_client.rate_limit.limit,
    "ratelimit-remaining": self._api_client.rate_limit.remaining,
    "ratelimit-reset": self._api_client.rate_limit.reset
}
```

So `client.rate_limit.limit` raises `AttributeError`. The actual keys are also named differently (`"ratelimit-limit"` vs `limit`). Either the implementation needs to return the `RateLimit` object directly, or the docs need updating. The fix in `client.py` would be:
```python
@property
def rate_limit(self):
    return self._api_client.rate_limit
```

**Contribution:** Fix the property to return the `RateLimit` object (already has `.limit`, `.remaining`, `.reset`) and update/verify the README example.

---

### Bug 2 — Bare `except:` in webhooks.py

**File:** `gocardless_pro/webhooks.py` line 12  
**Severity:** Low — bad practice, masks unexpected errors

```python
try:
    basestring
except:          # catches EVERYTHING, including KeyboardInterrupt, SystemExit
    basestring = str
```

This should be:
```python
try:
    basestring
except NameError:
    basestring = str
```

`basestring` doesn't exist in Python 3 — a `NameError` is the only expected exception here. Catching everything silently swallows any other unexpected errors during module import.

**Contribution:** One-line fix, easy first PR.

---

### Bug 3 — Python 2 print syntax in docstring example

**File:** `gocardless_pro/client.py` line 26  
**Severity:** Low — misleading docs

The module docstring contains:
```python
print '{} {}'.format(customer.family_name, customer.given_name)
```

This is Python 2 syntax and will confuse anyone copying from the docs. Should be:
```python
print('{} {}'.format(customer.family_name, customer.given_name))
```

**Contribution:** Trivial fix, good first contribution with clear justification (Python 2 EOL, library only supports Python 3.8+).

---

### Issue 4 — Unused `six` dependency in setup.py

**File:** `setup.py`  
**Severity:** Low — unnecessary install for all users

```python
install_requires=['requests>=2.6', 'six']
```

`six` is a Python 2/3 compatibility shim. It is never imported anywhere in the codebase. The library only supports Python 3.8+, so `six` serves no purpose and adds a dependency for all users.

**Contribution:** Remove `six` from `install_requires`. Also worth checking if `six` was the reason for the bare `except` pattern in `webhooks.py` (a common `six` use case) and cleaning that up together.

---

### Issue 5 — Missing test coverage for Paginator

**File:** No direct unit tests for `gocardless_pro/paginator.py`  
**Severity:** Medium — core feature untested in isolation

The `Paginator` class is only tested indirectly through integration tests. There are no unit tests covering:
- Empty first page (no records)
- Single page (no `after` cursor)
- `before` cursor behavior
- Behavior when a page fetch fails mid-iteration
- `ListResponse.before` and `ListResponse.after` properties

**Contribution:** Add `tests/paginator_test.py` with unit tests using the `responses` mock library (already a dev dependency).

---

### Issue 6 — No type hints

**File:** All source files  
**Severity:** Medium — developer experience

The library supports Python 3.8+ but has zero type annotations. No `py.typed` marker, no `.pyi` stubs. This means no IDE autocompletion, no `mypy` support, and no `pyright` checks for users.

**Contribution:** Add type hints to the hand-written files first (`client.py`, `api_client.py`, `errors.py`, `paginator.py`, `webhooks.py`, `rate_limit.py`) since the generated `services/` and `resources/` files would get overwritten. Then open a discussion about adding a `py.typed` marker.

---

## What NOT to Contribute (Generated Code)

Almost every file in `gocardless_pro/services/` and `gocardless_pro/resources/` has this header:

```
# WARNING: Do not edit by hand, this file was generated by Crank
```

Crank is GoCardless's internal code generator. Any manual edits to those files will be overwritten when they regenerate. Don't open PRs that modify generated files unless you're fixing something in the generator template or the build process adds a post-generation fix step.

**Safe to contribute to (hand-written):**
- `client.py`
- `api_client.py`
- `errors.py`
- `paginator.py`
- `list_response.py`
- `rate_limit.py`
- `webhooks.py`
- `base_service.py`
- All test files in `tests/`
- `README.rst`, `setup.py`

---

## Quick Wins (Ranked by Effort vs. Impact)

| # | Fix | Effort | Impact |
|---|---|---|---|
| 1 | Bare `except` → `except NameError` in `webhooks.py` | 5 min | Low/Good practice |
| 2 | Python 2 print syntax fix in `client.py` docstring | 5 min | Low/Docs |
| 3 | Remove `six` from `setup.py` | 5 min | Low/Cleanup |
| 4 | Fix `rate_limit` property to return object not dict | 30 min | High/Bug fix |
| 5 | Add `tests/paginator_test.py` | 2–3 hrs | Medium/Coverage |
| 6 | Add type hints to hand-written files | Days | High/DX |

---

## How to Run Tests

```bash
pip install -r requirements-dev.txt
pytest tests/
```

Or with tox for multi-version:
```bash
tox
```

Or via Docker (per Makefile):
```bash
make test
```
