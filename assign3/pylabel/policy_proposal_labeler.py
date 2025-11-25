'''
Create and use the labeler

Label: "Potential Misinformation"

Criteria: Posts that contain pseudo-scientific claims about transgender people.

'''

import os
import time
import pandas as pd
from atproto import Client
from dotenv import load_dotenv
import requests

load_dotenv()

# GLOBAL VARS 
PERSPECTIVE_API_KEY = os.getenv("PERSPECTIVE_API_KEY")
THRESHOLD = 0.6 # for now 
keyword_file = "../labeler-inputs/input-data-keywords.csv"
keywords_df = pd.read_csv(keyword_file, header=None, names=["Keyword"])
KEYWORDS = keywords_df["Keyword"].tolist()
LABEL = "Potential Misinformation"

# 1. Make sure post surrounds trans issues. We will not analyze anything that is not related to trans issues.
# use simple keyword filtering similar to getting trans related data in data_scraper.py
def is_trans_related(text):
    """
    Returns 1 if text contains any trans-related keyword, else 0.
    """
    text_lower = str(text).lower()
    return int(any(keyword in text_lower for keyword in KEYWORDS))

# 2. 


# OUTPUT TO NEW LABELED DATA FILE 
df = pd.read_csv("../test-data/data.csv")

labels = []
for idx, row in df.iterrows():
    label = is_trans_related(row["Original Text"])
    labels.append(label)
    time.sleep(0.1)  # avoid hitting API limits
    if idx % 10 == 0:
        print(f"Labeled {idx+1}/{len(df)} posts")

df["Label"] = labels  # add new column for binary label

# Save new CSV
output_file = "labeled_data.csv"
df.to_csv(output_file, index=False)








