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


# 2. Perspective API - get toxicity score 
def get_toxicity_score(text, retries=3):
    """Call Perspective API and return toxicity score (0-1)"""
    url = "https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze"
    data = {
        "comment": {"text": str(text)},
        "languages": ["en"],
        "requestedAttributes": {"TOXICITY": {}}
    }
    params = {"key": PERSPECTIVE_API_KEY}

    for attempt in range(retries):
        try:
            response = requests.post(url, json=data, params=params)
            response.raise_for_status()
            return response.json()["attributeScores"]["TOXICITY"]["summaryScore"]["value"]
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                print("Rate limit hit. Retrying...")
                time.sleep(1 + attempt)  # exponential backoff
            else:
                print(f"Error: {e}")
                break
    return None


# OUTPUT TO NEW LABELED DATA FILE 
df = pd.read_csv("../test-data/data.csv")

relevancies = []
toxicity_scores = []
for idx, row in df.iterrows():
    # run checks
    relevant = is_trans_related(row["Original Text"])
    # score = get_toxicity_score(row["Original Text"]) DO NOT RUN THIS IF YOU ALREADY HAVE LABELED DATA

    # append to list 
    toxicity_scores.append(score)
    relevancies.append(relevant)
    time.sleep(0.1)  # avoid hitting API limits

    if idx % 10 == 0:
        print(f"Labeled {idx+1}/{len(df)} posts")

df["Is Related"] = relevancies
df["Toxicity"] = toxicity_scores


# Save new CSV
output_file = "labeled_data.csv"
df.to_csv(output_file, index=False)








