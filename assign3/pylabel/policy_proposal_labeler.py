# Harm: misinformation that cites pseudo-science to delegitimize transgender identities. 
# labels it as misinformation so the general public does NOT get misinformed about invalid claims with no scientific basis

# 1. scrape off of bluesky posts that are about being trans/trans identity through the keywords. we will use this to train our label.
import os
import time
import pandas as pd
from atproto import Client
from dotenv import load_dotenv

load_dotenv()
USERNAME = os.getenv("USERNAME")
PW = os.getenv("PW")

keyword_file = "../labeler-inputs/input-data-keywords.csv"
keywords_df = pd.read_csv(keyword_file, header=None, names=["Keyword"])
KEYWORDS = keywords_df["Keyword"].tolist()

client = Client()
client.login(USERNAME, PW)

all_posts = list()
seen_urls = set()

for keyword in KEYWORDS:
    try:
        print(f"Searching posts for keyword: {keyword}")
        # Fetch posts
        res = client.app.bsky.feed.search_posts(params={"q": keyword, "limit": 50})

        for post in res.posts:
            url = f"https://bsky.app/profile/{post.author.handle}/post/{post.uri.rsplit('/',1)[-1]}"
            if url in seen_urls:
                continue
            seen_urls.add(url)
            all_posts.append({
                "URL": url,
                "Text": post.record.text,
                "Keyword": keyword
            })

        # Sleep to avoid rate limiting
        time.sleep(1)

    except Exception as e:
        print(f"Error fetching keyword '{keyword}': {e}")
        continue


# filter to see whether post is about the trans identity
# filter to see whether post is part of test data set. we do not want the same posts from the test set in the training set. 
TRANS_TERMS = ["trans", "transgender", "trans man", "trans woman", "transition", "gender affirming"]
def is_about_trans(text):
    text_lower = text.lower()
    return any(term in text_lower for term in TRANS_TERMS)

test_df = pd.read_csv("../test-data/test-posts.csv")
test_urls = set(test_df["Post Link"].tolist())


filtered_posts = [
    post for post in all_posts
    if is_about_trans(post["Text"]) and post["URL"] not in test_urls
]


df = pd.DataFrame(filtered_posts)
df.to_csv("data.csv", index=False)
print(f"Saved {len(filtered_posts)} posts to data.csv")