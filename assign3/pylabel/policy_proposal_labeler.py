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
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from groq import Groq
import json
import re

load_dotenv()

# GLOBAL VARS 
PERSPECTIVE_API_KEY = os.getenv("PERSPECTIVE_API_KEY")
THRESHOLD = 0.6 # for now 
keyword_file = "../labeler-inputs/input-data-keywords.csv"
keywords_df = pd.read_csv(keyword_file, header=None, names=["Keyword"])
KEYWORDS = keywords_df["Keyword"].tolist()
LABEL = "Potential Misinformation"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)


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

# 3. LLaMA: determine misinformation through model
from groq import Groq

client = Groq()

def get_misinformation_score_groq(post_text):
    """
    Gets a 0-3 misinformation score using groq/compound.
    Returns an int or None if the API fails.
    """
    prompt = f"""
Rate the following text for misinformation about trans people on a 0-3 scale:
0 = No incorrect facts
1 = Minor incorrect facts
2 = Some incorrect facts
3 = Major incorrect facts
Return only the integer score.

Text: "{post_text}"

Return only the integer score 0,1,2, or 3. Do NOT include an explanation. Number only.
"""

    try:
        # Call groq/compound
        completion = client.chat.completions.create(
            model="groq/compound",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_completion_tokens=10,
            top_p=1,
            stream=False,
        )

        # Extract the assistant content
        raw_response = completion.choices[0].message.content.strip()
        match = re.search(r'\d+', raw_response)
        if match:
            score = int(match.group())
        else:
            score = None  # no valid number found
        
        return score

    except Exception as e:
        print(f"Error calling Groq API: {e}")
        return None



 

# OUTPUT TO NEW LABELED DATA FILE 
df = pd.read_csv("../test-data/data.csv")

relevancies = []
toxicity_scores = []
misinfo_scores = []
for idx, row in df.iterrows():
    # run checks

    # relevant = is_trans_related(row["Original Text"])
    # score = get_toxicity_score(row["Original Text"]) DO NOT RUN THIS IF YOU ALREADY HAVE LABELED DATA
    # misinfo_score = get_misinformation_score_groq(row["Original Text"])
   

    # append to list 
    # toxicity_scores.append(score)
    # relevancies.append(relevant)
    # misinfo_scores.append(misinfo_score)

    time.sleep(0.1)  # avoid hitting API limits

    if idx % 10 == 0:
        print(f"Labeled {idx+1}/{len(df)} posts")

# df["Is Related"] = relevancies
# df["Toxicity"] = toxicity_scores
# df["Misinfo Score"] = misinfo_scores


# Save new CSV
output_file = "labeled_data.csv"
df.to_csv(output_file, index=False)








