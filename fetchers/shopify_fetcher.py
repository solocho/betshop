import requests
import json
import os

def load_shopify_credentials():
    with open(os.path.join('config', 'secrets.json')) as f:
        secrets = json.load(f)
    return secrets['shopify']['store_url'], secrets['shopify']['access_token']

def fetch_latest_products(limit=10):
    store_url, access_token = load_shopify_credentials()
    url = f"https://{store_url}/admin/api/2023-01/products.json?limit={limit}"
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        products = response.json().get("products", [])
        # Add price from first variant to product dict
        for p in products:
            p["price"] = p["variants"][0]["price"] if p.get("variants") else "N/A"
        return products
    else:
        print(f"Error fetching products: {response.status_code} - {response.text}")
        return []

if __name__ == "__main__":
    latest = fetch_latest_products()
    for product in latest:
        print(f"{product['title']} - ₦{product['price']}")
