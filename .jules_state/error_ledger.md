| Timestamp | Error Type | Description | Fix Applied | Lesson Learned |
|---|---|---|---|---|
| 2025-12-29 14:31 | Selector Error | Strict mode violation: locator("h1") resolved to 3 elements in harvester.py | Scoped h1 selector to div[role='main'] and added error handling | Google Maps DOM has multiple h1 elements (Results, Sponsored). Use more specific containers. |
| 2025-12-29 14:34 | Timeout Error | Locator.wait_for: Timeout 5000ms exceeded for h1 | Changed strategy to extract name from list item aria-label before clicking | H1 in details pane might be hidden or hard to select reliably. List item metadata is more stable. |
| 2025-12-29 14:39 | URL Error | Protocol error (Page.navigate): Cannot navigate to invalid URL in enrichment.py | Extracted URLs from Google Maps are redirected (google.com/url?q=...). Need to clean them. | Google Maps often wraps external links in a redirection URL. Always inspect and clean extracted URLs. |
