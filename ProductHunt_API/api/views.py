from datetime import timezone

from django.shortcuts import render
import requests
from datetime import datetime, timedelta
from rest_framework.decorators import api_view
from rest_framework.response import Response
import json

# Create your views here.

PRODUCTHUNT_API_URL = "https://api.producthunt.com/v2/api/graphql"
# PRODUCTHUNT_API_KEY = "Bearer iuG0MURNy1YqwqbpXqWeRPc6fVhb3ON2l6h-5RmB7Bw"
PRODUCTHUNT_BEARER_TOKEN = "bASP0mjCahq5C207aPZA3cywFmnrR_33x2Q2TWYD4SE"

GRAPHQL_QUERY = """
query($after: String) {
  posts(order: VOTES, first: 20, after: $after) {
    pageInfo {
      hasNextPage
      endCursor
    }
    edges {
      node {
        name
        tagline
        description
        votesCount
        commentsCount
        createdAt
        url
        topics {
          edges {
            node {
              name
            }
          }
        }
      }
    }
  }
}
"""


def extract_posts(response_data):
    return [edge["node"] for edge in response_data.get("data", {}).get("posts", {}).get("edges", [])]


def filter_by_keywords(posts, keywords):
    keywords = [k.lower() for k in keywords]
    result = []
    for post in posts:
        topics = post.get("topics", {}).get("edges", [])
        topic_names = [t["node"]["name"].lower() for t in topics]
        matched_keywords = [k for k in keywords if any(k in t or t in k for t in topic_names)]

        print(f"Post: {post['name']}")
        print(f"Topics: {topic_names}")
        print(f"Keywords: {keywords}")
        print(f"Matched keywords: {matched_keywords}")

        if matched_keywords:
            print("=> This post matched!")
            result.append(post)
    return result


@api_view(["POST"])
def producthunt_filter(request):
  keywords = request.data.get("keywords", [])
  max_pages = request.data.get("max_pages", 10)

  if not keywords or not isinstance(keywords, list):
    return Response({"error": "Please provide a list of keywords."}, status=400)

  if not isinstance(max_pages, int) or max_pages <= 0:
    return Response({"error": "Invalid value for max_pages. It must be a positive integer."}, status=400)

  after = None
  has_next_page = True
  all_posts = []
  request_count = 0

  print("=== Start fetching from ProductHunt ===")
  while has_next_page and request_count < max_pages:
    request_count += 1
    print(f"\nRequest #{request_count}...")

    headers = {
      "Authorization": f"Bearer {PRODUCTHUNT_BEARER_TOKEN}",
      "Accept": "application/json",
      "Content-Type": "application/json",
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
      "Origin": "https://www.producthunt.com",
      "Referer": "https://www.producthunt.com/",
      "Accept-Language": "en-US,en;q=0.9"
    }
    payload = {"query": GRAPHQL_QUERY, "variables": {"after": after}}
    print("Outgoing headers:", headers)
    print("Outgoing payload:", json.dumps(payload))

    response = requests.post(
      PRODUCTHUNT_API_URL,
      json=payload,
      headers=headers
    )

    print("Response status:", response.status_code)
    if response.status_code != 200:
      print("Response text:", response.text)
      return Response({"error": "ProductHunt API error", "details": response.text}, status=500)

    try:
      data = response.json()
    except Exception as e:
      print("JSON decode error:", str(e))
      print("Raw response:", response.text)
      return Response({"error": "ProductHunt API error", "details": "Invalid JSON response", "raw": response.text}, status=500)

    posts = extract_posts(data)
    print(f"Got {len(posts)} posts in this request")
    all_posts.extend(posts)

    page_info = data.get("data", {}).get("posts", {}).get("pageInfo", {})
    has_next_page = page_info.get("hasNextPage", False)
    after = page_info.get("endCursor")

  print("\n=== Finished fetching ===")
  print(f"Total collected posts: {len(all_posts)}")

  matched_posts = filter_by_keywords(all_posts, keywords)
  print(f"After keyword filter: {len(matched_posts)}")

  # Simplify topics
  for post in matched_posts:
    post["topics"] = [t["node"]["name"] for t in post.get("topics", {}).get("edges", [])]

  return Response(matched_posts)

@api_view(["GET"])
def health_check(request):
    return Response({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()})