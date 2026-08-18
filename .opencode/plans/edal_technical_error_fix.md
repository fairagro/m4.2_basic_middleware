# Fix Plan: edal - Handle HttpSessionTechnicalError as recoverable

## Issue
The edal repository (335 URLs) has 191 URLs returning 500/503/timeout errors from the IPK server. The middleware treats `HttpSessionTechnicalError` as an "unrecoverable exception" and skips the ENTIRE repository (valid_entries: 0, skipped: true).

## Root Cause
In `middleware/metadata_scraper/__init__.py`, the `_extract_metadata` function (lines 75-91) only catches:
- `HttpSessionResponseError` (4xx)
- `HttpSessionDecodeError` (decoding issues)

But NOT `HttpSessionTechnicalError` (5xx, timeouts, network errors) which is raised by `session.get_decoded_url` for server errors.

When `HttpSessionTechnicalError` bubbles up to `_extract_many_metadata`, it's treated as "unrecoverable" and the whole repo is skipped.

## Fix
Modify `_extract_metadata` in `middleware/metadata_scraper/__init__.py` to also catch `HttpSessionTechnicalError` and return `None` (skip that single dataset).

```python
except (HttpSessionResponseError, HttpSessionDecodeError, HttpSessionTechnicalError) as e:
```

## Files to Change
- `middleware/metadata_scraper/__init__.py` (line 81)

## Verification
Run the edal scrape again - should get ~144 valid entries (335 - 191) instead of 0.