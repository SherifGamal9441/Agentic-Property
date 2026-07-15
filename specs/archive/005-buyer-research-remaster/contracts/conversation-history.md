# Conversation History Contract

## `GET /api/conversations/{thread_id}`

Returns the saved transcript for one validated opaque browser thread. This endpoint does not list sessions and never accepts a user identity.

### Success response

```json
{
  "thread_id": "8f9d67d9-61de-44d9-a95d-8d0c5c8a9d4f",
  "messages": [
    {"role": "user", "content": "A ready 2BR in Dubai Marina"},
    {"role": "assistant", "content": "I found active dataset matches..."}
  ]
}
```

### Empty or unknown thread

Return a 404 response with a safe buyer-facing message. Do not expose checkpoint internals, database paths, or other thread metadata.

### Validation

`thread_id` must be a UUID. Each message must be one of `user` or `assistant` with a string content value. The server returns no internal graph state beyond the transcript.
