import os
import json
from fetchers.shopify_fetcher import fetch_latest_products
from generators.content_generator import generate_social_post

CACHE_DIR = 'cache'
OUTPUT_FILE = 'latest_generated_posts.json'

def already_done(product_id):
    return os.path.exists(os.path.join(CACHE_DIR, f'{product_id}.json'))

def generate_posts_for_new_products(batch_size=10):
    products = fetch_latest_products(limit=50)  # Fetch a bigger batch just in case
    new_posts = []

    count = 0
    for product in products:
        pid = product.get('id')
        if already_done(pid):
            continue  # Skip products already processed

        post = generate_social_post(product)
        # Find first image, if any
        image_url = product.get('image', {}).get('src') if product.get('image') else None

        new_posts.append({
            "product_id": pid,
            "title": product['title'],
            "post": post,
            "image_url": image_url
        })

        count += 1
        if count >= batch_size:
            break

    if new_posts:
        # Save to a JSON file for future use
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_posts, f, ensure_ascii=False, indent=2)
        print(f"\nSaved {len(new_posts)} new posts to {OUTPUT_FILE}")
    else:
        print("\nNo new products found to generate posts for.")

if __name__ == "__main__":
    generate_posts_for_new_products(batch_size=10)
