# Twitter API Proxy

This service provides a proxy for accessing Twitter posts data through an external API.

## Endpoints

### POST /search/twitter
Search for Twitter posts using form data (matches the original curl format).

**Parameters:**
- `keywords[]`: List of keywords to search for
- `post_type`: Type of posts - "Top" or "Latest" (default: "Top")

### GET /search/twitter
Alternative GET endpoint for Twitter search.

**Parameters:**
- `keywords`: Comma-separated keywords
- `post_type`: Type of posts - "Top" or "Latest" (default: "Top")

### GET /health
Health check endpoint.

## Usage Examples

```bash
# Using POST (form data)
curl -X POST "http://localhost:8004/search/twitter" \
  -F 'keywords=تهران' \
  -F 'post_type=Top'

# Using GET
curl "http://localhost:8004/search/twitter?keywords=تهران&post_type=Top"
```

## Running the Service

```bash
python main.py
```

The service will be available at `http://localhost:8004`