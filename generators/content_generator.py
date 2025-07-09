import openai
import json
import os

def load_openai_key():
    with open(os.path.join('config', 'secrets.json')) as f:
        secrets = json.load(f)
    return secrets['openai']['api_key']

def get_cache_path(product_id):
    cache_dir = 'cache'
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, f'{product_id}.json')

def generate_social_post(product):
    product_id = product.get('id')
    cache_path = get_cache_path(product_id)

    # Check cache first!
    if os.path.exists(cache_path):
        with open(cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['post']

    openai.api_key = load_openai_key()
    price = product.get('price', 'N/A')
    title = product.get('title', 'Fashion Item')
    description = product.get('body_html', '')[:200]

    prompt = (
        f"Write a perfect Instagram/Facebook marketing post for Bettsiddy Collections, an online fashion store. "
        f"The post must mention 'Bettsiddy Collections', the product name '{title}', and the price (₦{price}). "
        f"Highlight why it's a must-have for fashion lovers, and add a strong call-to-action like 'Shop now at Bettsiddy Collections!'. "
        f"Make it energetic, exclusive, and use 2-3 relevant emojis. "
        f"Product Description: {description}"
    )

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a creative social media marketer for Bettsiddy Collections, a Nigerian online fashion store."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=120,
        temperature=0.9
    )
    post_text = response.choices[0].message.content.strip()

    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump({'post': post_text}, f)

    return post_text

if __name__ == "__main__":
    # Test with a fake product
    sample_product = {
        "id": 1234567890,
        "title": "Printed Hoodie",
        "price": "6999",
        "body_html": "This hoodie is soft, stylish, and perfect for fall."
    }
    print(generate_social_post(sample_product))
