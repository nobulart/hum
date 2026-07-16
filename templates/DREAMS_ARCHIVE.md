# DREAMS_ARCHIVE.md

Minimal tombstones for dismissed or superseded fragments. A tombstone prevents
unnecessary rediscovery without retaining the full discarded content.

Tombstone format — YAML front matter per entry:

```yaml
---
id: dream-YYYYMMDDThhmmss-XXXX
dismissed_at: YYYY-MM-DD
reason: deferred_then_exhausted | contradicted_by | duplicated | obsolete | low_value
content_hash: <sha1-12>
---
```

## Tombstones
