# ProductHunt Filter API

A Django REST API that filters ProductHunt posts based on keywords. This application fetches posts from ProductHunt's GraphQL API and filters them by matching keywords against post topics.

## Features

- Fetch posts from ProductHunt using their GraphQL API
- Filter posts by keywords matching their topics
- Pagination support for fetching multiple pages
- Case-insensitive partial keyword matching
- Docker support for easy deployment

## Tech Stack

- **Backend**: Django 5.2.5 with Django REST Framework
- **Database**: SQLite (default)
- **External API**: ProductHunt GraphQL API
- **Containerization**: Docker & Docker Compose

## Quick Start

### Using Docker (Recommended)

1. **Clone and navigate to the project directory**
   ```bash
   cd /path/to/producthunt-main
   ```

2. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

3. **The API will be available at:**
   ```
   http://localhost:8910
   ```

### Using Python Directly

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run migrations (if needed)**
   ```bash
   python manage.py migrate
   ```

3. **Start the development server**
   ```bash
   python manage.py runserver 8910
   ```

## API Documentation

### Base URL
```
http://localhost:8910
```

### Endpoints

#### POST `/api/producthunt/filter/`

Filters ProductHunt posts based on provided keywords.

**Request**

- **URL**: `/api/producthunt/filter/`
- **Method**: `POST`
- **Content-Type**: `application/json`

**Request Body Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `keywords` | array | Yes | List of keywords to filter posts by topics |
| `max_pages` | integer | No | Maximum pages to fetch (default: 10, max recommended: 20) |

**Request Example**
```json
{
    "keywords": ["ai", "productivity", "saas"],
    "max_pages": 5
}
```

**Response**

Returns an array of filtered ProductHunt posts.

**Response Fields**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Product name |
| `tagline` | string | Product tagline |
| `description` | string | Product description |
| `votesCount` | integer | Number of votes |
| `commentsCount` | integer | Number of comments |
| `createdAt` | string | Creation timestamp (ISO 8601) |
| `url` | string | ProductHunt URL |
| `topics` | array | List of topic names |

**Response Example**
```json
[
    {
        "name": "AI Assistant Pro",
        "tagline": "Your intelligent productivity companion",
        "description": "An AI-powered tool that helps boost your productivity...",
        "votesCount": 342,
        "commentsCount": 28,
        "createdAt": "2024-10-13T10:30:00Z",
        "url": "https://www.producthunt.com/posts/ai-assistant-pro",
        "topics": ["AI", "Productivity", "SaaS", "Automation"]
    }
]
```

**Error Responses**

- **400 Bad Request**: Invalid request parameters
  ```json
  {
      "error": "Please provide a list of keywords."
  }
  ```

- **500 Internal Server Error**: ProductHunt API error
  ```json
  {
      "error": "ProductHunt API error",
      "details": "API error details"
  }
  ```

## Usage Examples

### Using cURL

```bash
curl -X POST http://localhost:8910/api/producthunt/filter/ \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["ai", "machine learning"],
    "max_pages": 3
  }'
```

### Using JavaScript (Fetch API)

```javascript
async function fetchProductHuntPosts() {
  try {
    const response = await fetch('http://localhost:8910/api/producthunt/filter/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        keywords: ['ai', 'productivity', 'automation'],
        max_pages: 5
      })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('Filtered posts:', data);
    return data;
  } catch (error) {
    console.error('Error fetching posts:', error);
  }
}

fetchProductHuntPosts();
```

### Using Python (requests)

```python
import requests
import json

url = 'http://localhost:8910/api/producthunt/filter/'
data = {
    'keywords': ['blockchain', 'crypto', 'web3'],
    'max_pages': 4
}

response = requests.post(url, json=data)

if response.status_code == 200:
    posts = response.json()
    print(f"Found {len(posts)} matching posts")
    for post in posts:
        print(f"- {post['name']}: {post['tagline']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

## How It Works

### Architecture

```
Client Request → Django API → ProductHunt GraphQL API → Filter & Process → Response
```

### Process Flow

1. **Input Validation**: Validates request parameters (keywords array, max_pages integer)

2. **ProductHunt API Integration**: 
   - Uses ProductHunt's GraphQL API with Bearer token authentication
   - Fetches posts ordered by votes with pagination support
   - Retrieves post details including name, tagline, description, votes, comments, and topics

3. **Keyword Filtering**:
   - Extracts topics from each post
   - Performs case-insensitive partial matching against provided keywords
   - A post matches if any of its topics contains any of the provided keywords

4. **Data Processing**:
   - Simplifies nested GraphQL response structure
   - Converts topics from nested objects to simple string arrays
   - Returns clean, filtered dataset

### Filtering Logic

The keyword matching uses partial, case-insensitive comparison:

```python
# Example: keyword "ai" matches topics like "AI", "Artificial Intelligence", "OpenAI"
matched = any(keyword.lower() in topic.lower() or topic.lower() in keyword.lower() 
              for topic in post_topics for keyword in user_keywords)
```

## Configuration

### Environment Variables

The application uses the following configuration:

- **ProductHunt API**: Uses GraphQL endpoint with Bearer token authentication
- **Debug Mode**: Enabled by default (set `DEBUG = False` for production)
- **Allowed Hosts**: Set to `['*']` (configure properly for production)

### Customization

#### Modify Fetch Limits

Edit `api/views.py` to change default pagination:

```python
# Change default max_pages
max_pages = request.data.get("max_pages", 20)  # Default changed to 20

# Change posts per page (currently 20)
# Modify the GraphQL query: first: 50
```

#### Add New Fields

To include additional ProductHunt post fields, modify the GraphQL query in `api/views.py`:

```graphql
query($after: String) {
  posts(order: VOTES, first: 20, after: $after) {
    edges {
      node {
        name
        tagline
        # Add new fields here
        website
        thumbnail {
          url
        }
        # ... existing fields
      }
    }
  }
}
```

## Project Structure

```
producthunt-main/
├── api/                    # Main API application
│   ├── __init__.py
│   ├── views.py           # API endpoint logic
│   ├── urls.py            # API URL routing
│   ├── models.py          # Database models (currently empty)
│   └── migrations/        # Database migrations
├── producthunt/           # Django project configuration
│   ├── __init__.py
│   ├── settings.py        # Django settings
│   ├── urls.py           # Main URL configuration
│   └── wsgi.py           # WSGI configuration
├── docker-compose.yml     # Docker Compose configuration
├── Dockerfile            # Docker image definition
├── requirements.txt      # Python dependencies
├── manage.py            # Django management script
└── db.sqlite3          # SQLite database file
```

## Development

### Adding New Features

1. **New Endpoints**: Add routes in `api/urls.py` and implement views in `api/views.py`
2. **Database Models**: Define models in `api/models.py` and create migrations
3. **Custom Filters**: Extend the filtering logic in the `filter_by_keywords` function

### Running Tests

```bash
python manage.py test
```

### Making Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

## Deployment Considerations

### Production Settings

Before deploying to production:

1. **Security**: 
   - Change `SECRET_KEY` in `settings.py`
   - Set `DEBUG = False`
   - Configure `ALLOWED_HOSTS` properly

2. **Database**: 
   - Consider using PostgreSQL or MySQL instead of SQLite
   - Configure database settings in `settings.py`

3. **Static Files**: 
   - Configure static file serving
   - Set `STATIC_ROOT` and run `collectstatic`

### Docker Production

For production deployment, modify `docker-compose.yml`:

```yaml
services:
  web:
    build: .
    ports:
      - "80:8910"
    environment:
      - DEBUG=False
    # Add volume for production database
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Find and kill process using port 8910
   lsof -ti:8910 | xargs kill -9
   ```

2. **Docker Build Issues**
   ```bash
   # Clean Docker cache
   docker system prune -a
   docker-compose up --build --force-recreate
   ```

3. **ProductHunt API Errors**
   - Check if the Bearer token is still valid
   - Verify internet connection
   - Check ProductHunt API status

### Logs

View detailed logs when running:
- **Docker**: `docker-compose logs -f`
- **Direct Python**: Logs appear in terminal with `DEBUG = True`

## API Rate Limits

- ProductHunt API has rate limits
- Recommended to keep `max_pages` ≤ 10 for optimal performance
- Each page fetches 20 posts, so `max_pages: 10` = up to 200 posts

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and add tests
4. Submit a pull request

## License

This project is for educational and development purposes. Ensure compliance with ProductHunt's API terms of service when using in production.