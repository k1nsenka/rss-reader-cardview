#!/usr/bin/env python3
"""
Bootstrap script to discover and subscribe to RSS feeds via Miniflux API.
Usage: python bootstrap_feeds.py <url1> <url2> ...
"""

import os
import sys
import json
import requests
from urllib.parse import urlparse
import time

# Configuration
MINIFLUX_BASE_URL = os.environ.get('MINIFLUX_BASE_URL', 'http://miniflux:8080')
MINIFLUX_API_KEY = os.environ.get('MINIFLUX_API_KEY', '')

# Category mappings based on domain/keywords
CATEGORY_MAPPINGS = {
    'papers': [
        'arxiv.org', 'nature.com', 'science.org', 'plos.org', 
        'springer.com', 'ieee.org', 'acm.org', 'sciencedirect.com',
        'biorxiv.org', 'medrxiv.org', 'chemrxiv.org'
    ],
    'tech': [
        'github.com', 'stackoverflow.com', 'dev.to', 'medium.com',
        'hackernews', 'techcrunch.com', 'wired.com', 'arstechnica.com',
        'theverge.com', 'engadget.com', 'slashdot.org', 'zdnet.com',
        'infoq.com', 'dzone.com', 'thenewstack.io'
    ],
    'business': [
        'bloomberg.com', 'reuters.com', 'wsj.com', 'ft.com',
        'economist.com', 'forbes.com', 'businessinsider.com',
        'fortune.com', 'cnbc.com', 'marketwatch.com', 'seekingalpha.com',
        'hbr.org', 'mckinsey.com'
    ]
}

def check_api_connection():
    """Check if API is accessible."""
    headers = {
        'X-Auth-Token': MINIFLUX_API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(
            f"{MINIFLUX_BASE_URL}/v1/me",
            headers=headers,
            timeout=5
        )
        response.raise_for_status()
        print(f"Successfully connected to Miniflux API as user: {response.json()['username']}")
        return True
    except Exception as e:
        print(f"Error connecting to API: {e}", file=sys.stderr)
        return False

def get_category_for_url(url):
    """Determine category based on URL domain."""
    domain = urlparse(url).netloc.lower()
    
    for category, domains in CATEGORY_MAPPINGS.items():
        for cat_domain in domains:
            if cat_domain in domain:
                return category
    
    # Default to tech if no match
    return 'tech'

def ensure_category_exists(category_name):
    """Create category if it doesn't exist."""
    headers = {
        'X-Auth-Token': MINIFLUX_API_KEY,
        'Content-Type': 'application/json'
    }
    
    # First, check if category exists
    try:
        response = requests.get(
            f"{MINIFLUX_BASE_URL}/v1/categories",
            headers=headers
        )
        response.raise_for_status()
        categories = response.json()
        
        # Check if category already exists
        for cat in categories:
            if cat['title'].lower() == category_name.lower():
                print(f"Category '{category_name}' already exists with ID {cat['id']}")
                return cat['id']
        
        # Create new category
        response = requests.post(
            f"{MINIFLUX_BASE_URL}/v1/categories",
            headers=headers,
            json={'title': category_name}
        )
        response.raise_for_status()
        new_category = response.json()
        print(f"Created category '{category_name}' with ID {new_category['id']}")
        return new_category['id']
        
    except Exception as e:
        print(f"Error managing category '{category_name}': {e}", file=sys.stderr)
        return None

def discover_feeds(url):
    """Discover RSS feeds from a given URL."""
    headers = {
        'X-Auth-Token': MINIFLUX_API_KEY,
        'Content-Type': 'application/json'
    }
    
    print(f"\nDiscovering feeds from: {url}")
    
    try:
        response = requests.post(
            f"{MINIFLUX_BASE_URL}/v1/discover",
            headers=headers,
            json={'url': url},
            timeout=30
        )
        response.raise_for_status()
        feeds = response.json()
        
        if not feeds:
            print(f"No feeds found at {url}")
            return []
        
        print(f"Found {len(feeds)} feed(s):")
        for feed in feeds:
            print(f"  - {feed['title']}: {feed['url']}")
        
        return feeds
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"No feeds found at {url}")
        else:
            print(f"HTTP error discovering feeds: {e}", file=sys.stderr)
            print(f"Response: {e.response.text}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Error discovering feeds: {e}", file=sys.stderr)
        return []

def subscribe_to_feed(feed_url, category_id, title=None):
    """Subscribe to a feed and assign it to a category."""
    headers = {
        'X-Auth-Token': MINIFLUX_API_KEY,
        'Content-Type': 'application/json'
    }
    
    payload = {
        'feed_url': feed_url,
        'category_id': category_id
    }
    
    try:
        response = requests.post(
            f"{MINIFLUX_BASE_URL}/v1/feeds",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        feed = response.json()
        print(f"✓ Successfully subscribed to: {feed['title']}")
        return True
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 409:
            print(f"✓ Already subscribed to: {feed_url}")
            # Try to update the category
            update_feed_category(feed_url, category_id)
        else:
            print(f"✗ HTTP error subscribing to feed: {e}", file=sys.stderr)
            print(f"Response: {e.response.text}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"✗ Error subscribing to feed: {e}", file=sys.stderr)
        return False

def update_feed_category(feed_url, category_id):
    """Update the category of an existing feed."""
    headers = {
        'X-Auth-Token': MINIFLUX_API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        # First, find the feed
        response = requests.get(
            f"{MINIFLUX_BASE_URL}/v1/feeds",
            headers=headers
        )
        response.raise_for_status()
        feeds = response.json()
        
        for feed in feeds:
            if feed['feed_url'] == feed_url:
                # Update the feed's category
                response = requests.put(
                    f"{MINIFLUX_BASE_URL}/v1/feeds/{feed['id']}",
                    headers=headers,
                    json={'category_id': category_id}
                )
                response.raise_for_status()
                print(f"  → Updated category for existing feed")
                return True
        
    except Exception as e:
        print(f"  → Could not update category: {e}", file=sys.stderr)
    
    return False

def main():
    """Main function to process URLs from command line."""
    if len(sys.argv) < 2:
        print("Usage: python bootstrap_feeds.py <url1> <url2> ...")
        print("Example: python bootstrap_feeds.py https://news.ycombinator.com https://arxiv.org")
        sys.exit(1)
    
    if not MINIFLUX_API_KEY:
        print("Error: MINIFLUX_API_KEY environment variable not set", file=sys.stderr)
        print("Please set it in your .env file and restart the container", file=sys.stderr)
        sys.exit(1)
    
    # Check API connection
    print(f"Connecting to Miniflux at {MINIFLUX_BASE_URL}...")
    if not check_api_connection():
        print("Failed to connect to Miniflux API. Please check your configuration.", file=sys.stderr)
        sys.exit(1)
    
    # Ensure categories exist
    print("\nEnsuring categories exist...")
    category_ids = {}
    for category in ['papers', 'tech', 'business']:
        cat_id = ensure_category_exists(category)
        if cat_id:
            category_ids[category] = cat_id
    
    if not category_ids:
        print("Error: Could not create any categories", file=sys.stderr)
        sys.exit(1)
    
    # Process each URL
    urls = sys.argv[1:]
    total_subscribed = 0
    
    for url in urls:
        # Ensure URL has protocol
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Discover feeds
        feeds = discover_feeds(url)
        
        # Subscribe to each discovered feed
        for feed in feeds:
            category = get_category_for_url(feed['url'])
            if category in category_ids:
                if subscribe_to_feed(feed['url'], category_ids[category], feed.get('title')):
                    total_subscribed += 1
            
            # Small delay to avoid overwhelming the API
            time.sleep(0.5)
    
    print(f"\n✅ Total feeds subscribed: {total_subscribed}")

if __name__ == "__main__":
    main()