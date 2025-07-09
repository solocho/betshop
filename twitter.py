import tweepy

# --- Fill in your keys ---
API_KEY = "U9R6XUdGT8ZZefKBo1x6nheW6"
API_SECRET = "5tiO3Lh2S7W3SwzB2t1eC8sB9uW3ytyu36cqjgBqpucT0fxvrJ"
ACCESS_TOKEN = "1941982344220651520-43B3uf3yFdEe2HP4j85247ma2MFLvx"
ACCESS_TOKEN_SECRET = "nTxdob9GhSt9qCPnUoXAcaqSB37iDnJOv5uGMOIFm82QT"

# --- Authenticate ---
auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

# --- Post a tweet ---
tweet = "🚀 Automated test tweet from Bettsiddy Collections fashion bot! #FashionAI"
try:
    api.update_status(status=tweet)
    print("Success! Tweet posted.")
except Exception as e:
    print("Failed to post:", e)
