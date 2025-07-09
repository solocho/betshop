import json
import requests
import datetime
import openai

# --- Load credentials ---
with open('config/secrets.json', 'r') as f:
    secrets = json.load(f)

# Use .myshopify.com domain!
SHOPIFY_STORE_URL = secrets['shopify']['store_url']  # e.g. bettsiddycollections.myshopify.com
SHOPIFY_ACCESS_TOKEN = secrets['shopify']['access_token']
OPENAI_API_KEY = secrets['openai']['api_key']

# ----------- CONFIG -----------
BLOG_TOPICS = [
    "10 Must-Have Summer Fashion Trends",
    "How to Style Accessories for Any Occasion",
    "Sustainable Fashion: Why It Matters in 2025",
    "The Rise of Athleisure: Fashion Meets Comfort",
    "Color Psychology in Fashion: What Your Outfit Says About You"
]
# Set BLOG_TOPICS = None to prompt for topic each run

def pick_blog_topic():
    import random
    if BLOG_TOPICS:
        return random.choice(BLOG_TOPICS)
    else:
        return input("Enter a topic for the blog post: ").strip()

def generate_blog_post(topic, openai_api_key, min_words=1000):
    print(f"Generating blog post on: {topic}")
    client = openai.OpenAI(api_key=openai_api_key)
    prompt = (
        f"Write a detailed, informative, and engaging Shopify blog post on the topic: '{topic}'.\n"
        f"The post should be at least {min_words} words, with clear headings, subheadings, and practical tips for readers. "
        f"Make it original, relevant for 2025, and include a strong introduction and conclusion. End with a call to action to shop or subscribe."
    )
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
        max_tokens=4000
    )
    content = response.choices[0].message.content.strip()
    if len(content.split()) < min_words:
        followup_prompt = (
            f"Continue the above blog post on '{topic}', making sure the combined total is at least {min_words} words. "
            f"Continue from where you left off. Use headings and paragraphs."
        )
        followup = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": followup_prompt}
            ],
            temperature=0.85,
            max_tokens=3000
        )
        content += "\n\n" + followup.choices[0].message.content.strip()
    return content

def print_shopify_blogs(store_url, access_token):
    api_url = f"https://{store_url}/admin/api/2023-07/blogs.json"
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }
    resp = requests.get(api_url, headers=headers)
    print("DEBUG: Blog list status:", resp.status_code)
    if resp.status_code == 200:
        blogs = resp.json().get("blogs", [])
        if not blogs:
            print("No blogs found in your Shopify store.")
        else:
            print("Available Blogs:")
            for b in blogs:
                print(f"  id={b['id']}   title='{b['title']}'")
        return blogs
    else:
        print(f"Failed to fetch blogs: {resp.status_code} {resp.text}")
        return []

def post_to_shopify(title, body_html, store_url, access_token, blog_id):
    url = f"https://{store_url}/admin/api/2023-07/blogs/{blog_id}/articles.json"
    payload = {
        "article": {
            "title": title,
            "body_html": body_html,
            "published": True,
            "tags": "AI, AutoBlog, 2025"
        }
    }
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }
    resp = requests.post(url, headers=headers, data=json.dumps(payload))
    if resp.status_code == 201:
        print("✅ Blog post published to Shopify.")
        return resp.json()['article']['id']
    else:
        print(f"❌ Failed to post: {resp.status_code}")
        print(resp.text)
        return None

def extract_title_from_blog(blog_content):
    # Use first heading or first sentence as the title
    lines = blog_content.splitlines()
    for line in lines:
        if line.strip().startswith("#"):
            return line.replace("#", "").strip()
    # Else, just first sentence
    return lines[0][:80] + "..."

if __name__ == "__main__":
    # --- 1. Confirm correct store_url format ---
    if not SHOPIFY_STORE_URL.endswith(".myshopify.com"):
        print("ERROR: Your store_url must end with .myshopify.com for Shopify API!")
        print("Edit config/secrets.json and set:")
        print('"store_url": "your-store-name.myshopify.com"')
        exit(1)

    # --- 2. Show available blogs and get blog ID ---
    blogs = print_shopify_blogs(SHOPIFY_STORE_URL, SHOPIFY_ACCESS_TOKEN)
    if not blogs:
        print("No blogs available. Create a blog in your Shopify admin first.")
        exit(1)
    blog_id = blogs[0]['id']  # Use first blog (or set a specific one if you want)

    # --- 3. Generate blog content ---
    topic = pick_blog_topic()
    blog_content = generate_blog_post(topic, OPENAI_API_KEY, min_words=1000)

    # --- 4. Markdown to HTML ---
    import markdown
    blog_html = markdown.markdown(blog_content)

    # --- 5. Create title ---
    blog_title = extract_title_from_blog(blog_content)
    today = datetime.date.today().strftime("%b %d, %Y")
    full_title = f"{blog_title} ({today})"

    print(f"\nPosting blog: {full_title}\n")

    # --- 6. Post ---
    post_id = post_to_shopify(
        title=full_title,
        body_html=blog_html,
        store_url=SHOPIFY_STORE_URL,
        access_token=SHOPIFY_ACCESS_TOKEN,
        blog_id=blog_id
    )
    if post_id:
        print(f"Blog posted! Shopify article ID: {post_id}")
    else:
        print("Failed to post the blog. See error above.")
