# DREAMS_ARCHIVE.md

Minimal tombstones for dismissed or superseded fragments. A tombstone prevents
unnecessary rediscovery without retaining the full discarded content.

Tombstone format — YAML front matter per entry:

```yaml
---
id: dream-YYYY-MM-DD-NNN
dismissed_at: YYYY-MM-DD
reason: contradicted_by | duplicated | obsolete | low_value | superseded_by:ID
content_hash: <sha1-or-similar>
---
```

## Tombstones
