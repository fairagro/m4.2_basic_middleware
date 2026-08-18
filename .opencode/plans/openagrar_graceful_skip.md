# Fix Plan: openagrar_native - Graceful skip with clear Cloudflare error

## Issue
The openagrar_native sitemap URL returns Cloudflare JavaScript challenge page instead of JSON. All automated approaches fail (aiohttp, cloudscraper). Cannot fetch the dataset list.

## Solution: Option B - Graceful skip with clear error
Detect Cloudflare challenge page in the openagrar parser and skip with a clear, documented error message. This is consistent with the edal fix where we handle per-repo failures gracefully.

## Implementation
Modify `middleware/metadata_scraper/sitemap_parser/openagrar.py`:

1. In `datasets` property, after getting content, check if it's a Cloudflare challenge page
2. If detected, raise `SitemapParseError` with clear message about Cloudflare protection
3. The error will propagate up and the repo will be skipped (like edal)

## Detection Logic
Check for Cloudflare challenge indicators:
- Title contains "Security Check" or "Sicherheitsüberprüfung"
- Contains specific Cloudflare challenge JavaScript
- Content-Type is text/html instead of application/json

```python
def _is_cloudflare_challenge(content: str) -> bool:
    indicators = [
        "Security Check",
        "Sicherheitsüberprüfung", 
        "cf_challenge",
        "cf-turnstile",
        "cloudflare",
        "cf-mitigated",
    ]
    content_lower = content.lower()
    return any(ind.lower() in content_lower for ind in indicators)
```

## Files to Change
- `middleware/metadata_scraper/sitemap_parser/openagrar.py` - Add detection and clear error

## Verification
Run middleware with config.yml --no-git:
- openagrar_native should show: `skipped: true` with clear error message in logs
- Other repos should continue working (bonares, edal, publisso)

## Documentation
Add comment in config.yml explaining the limitation:
```yaml
#   - name: openagrar_native
#     url: "https://www.openagrar.de/servlets/solr/select?..."
#     sitemap: openagrar
#     # SKIPPED: Cloudflare JavaScript challenge blocks automated access.
#     # Requires headless browser (Playwright) or manual API access.
```

## Benefits
- No new dependencies
- Consistent error handling pattern
- Clear documentation for future maintainers
- Other 4 repos continue harvesting