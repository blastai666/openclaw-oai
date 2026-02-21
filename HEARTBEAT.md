# HEARTBEAT.md

# Keep this file empty (or with only comments) to skip heartbeat API calls.

# Add tasks below when you want the agent to check something periodically.

## Self-Reflection Check (required)
Run `self-reflection check` at each heartbeat.
If ALERT: read past lessons, reflect, then log insights.

Commands:
- `self-reflection check [--quiet]` - Check if reflection is due
- `self-reflection read [n]` - Read last n reflections (default: 5)
- `self-reflection log <tag> <miss> <fix>` - Log a new reflection
- `self-reflection stats` - Show statistics
