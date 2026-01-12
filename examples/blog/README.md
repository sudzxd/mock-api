# Blog Example

Multi-model API demonstrating relationships between User, Post, and Comment models.

## Models

- **User**: Blog authors with username and bio
- **Post**: Blog posts with `author_id` foreign key to User
- **Comment**: Comments with `post_id` and `user_id` foreign keys

## Setup

### Local

```bash
mockapi-server serve --models models.py --generate-data --data-count 50
```

### Docker

```bash
docker-compose up
```

## Access

- API: http://localhost:3000/api/v1
- Docs: http://localhost:3000/docs

## Query Examples

```bash
# Get all posts by user 1
curl "http://localhost:3000/api/v1/posts?author_id=1"

# Get all comments on post 5
curl "http://localhost:3000/api/v1/comments?post_id=5"

# Get all comments by user 2
curl "http://localhost:3000/api/v1/comments?user_id=2"
```

See [examples documentation](../../docs/examples.md) for detailed usage patterns.
