# Label: Potential misnformation
# Category/Relevancy: Related to trans issues/trans rights/trans people, etc.
import os
import time
import json
import re
import requests 

import pandas as pd
from atproto import Client
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from groq import Groq

load_dotenv()

# GLOBAL VARS 
PERSPECTIVE_API_KEY = os.getenv("PERSPECTIVE_API_KEY")
THRESHOLD = 0.5
keyword_file = "../labeler-inputs/input-data-keywords.csv"
keywords_df = pd.read_csv(keyword_file, header=None, names=["Keyword"])
KEYWORDS = keywords_df["Keyword"].tolist()
LABEL = "Potential Misinformation"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)
test_df = pd.read_csv("../test-data/data.csv")
label_df = pd.read_csv("labeled_data.csv")


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
                wait_time = 1.1 * (attempt + 1)  # small backoff
                print(f"Rate limit hit. Retrying in {wait_time:.1f} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Error: {e}")
                break
    return None

# 3. LLaMA: determine misinformation through model
def get_misinformation_score_groq(post_text):
    """
    Gets a 0-3 misinformation score using llama 3.1 8b instant model
    Returns an int or None if the API fails.
    """
    client = Groq()
    prompt = f"""
Rate the following text for misinformation about trans people on a 0-3 scale:

0 = No incorrect facts
1 = Minor incorrect facts
2 = Some incorrect facts
3 = Major incorrect facts

Label as potential misinformation if the text contains any of these:
- False/misleading biological claims about sex/gender
- Claims framing trans identity as a mental disorder or delusion
- Misuse of science to delegitimize trans identities
- Harmful or unverified causal claims
- Broad biological/scientific claims lacking factual support

Text: "{post_text}"

Return only the integer 0,1,2,3. No explanation.
"""

    try:
        # Call groq/compound
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_completion_tokens=10,
            top_p=1,
            stream=False,
        )

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



'''
HELPER FUNCTIONS TO APPLY EACH API/ASSIGN LABELS
'''

def add_relevancies(df_file="labeled_data.csv"):
    label_df = pd.read_csv(df_file)
    new_posts = test_df[~test_df["Original Text"].isin(label_df["Original Text"])].copy()
    
    if new_posts.empty:
        print("No new posts to add for relevancy.")
        return label_df

    new_posts["Is Related"] = new_posts["Original Text"].apply(is_trans_related)

    combined_df = pd.concat([label_df, new_posts], ignore_index=True)
    combined_df.to_csv(df_file, index=False)
    print(f"Added {len(new_posts)} new relevancy labels.")
    return combined_df

def add_toxicity_scores(df_file="labeled_data.csv"):
    label_df = pd.read_csv(df_file)
    new_posts = label_df[label_df["Toxicity"].isna() | label_df["Toxicity"].isnull()].copy()
    
    if new_posts.empty:
        print("No new posts to score for toxicity.")
        return label_df
    
    toxicity_scores = []
    for idx, row in new_posts.iterrows():
        score = get_toxicity_score(row["Original Text"])
        toxicity_scores.append(score)

        if idx % 10 == 0:
            print(f"Toxicity: Labeled {idx+1}/{len(new_posts)} posts")
        
        time.sleep(0.3) # avoid hitting limits
    
    new_posts["Toxicity"] = toxicity_scores
    label_df.update(new_posts)
    label_df.to_csv(df_file, index=False)
    print(f"Updated misinformation scores for {len(new_posts)} posts.")
    return label_df


def add_misinformation_scores(df_file="labeled_data.csv"):
    label_df = pd.read_csv(df_file)
    new_posts = label_df[label_df["Misinformation"].isna() | label_df["Misinformation"].isnull()].copy()
    
    if new_posts.empty:
        print("No new posts to score for misinformation.")
        return label_df

    misinfo_scores = []
    for idx, row in new_posts.iterrows():
        score = get_misinformation_score_groq(row["Original Text"])
        misinfo_scores.append(score)

        if idx % 10 == 0:
            print(f"Misinfo: Labeled {idx+1}/{len(new_posts)} posts")
        
        # Sleep to avoid hitting API limits
        time.sleep(0.5)

    new_posts["Misinformation"] = misinfo_scores

    label_df.update(new_posts)
    label_df.to_csv(df_file, index=False)
    print(f"Updated misinformation scores for {len(new_posts)} posts.")
    return label_df

# 4. Calculate whether post exceeds threshold
def assign_labels():

    df = pd.read_csv("labeled_data.csv")
    labels = []
    for idx, row in pd.read_csv("labeled_data.csv").iterrows():
        if row["Is Related"] == 0:
            labels.append("Not misinformation (irrelevant)")
            continue 

        misinformation = row["Misinformation"] / 3  # 0–1
        toxicity = row["Toxicity"]  # 0–1

        risk = 0.7 * misinformation + 0.3 * toxicity

        label = "Potential Misinformation" if risk > THRESHOLD else "Nothing detected"
        labels.append(label)

    df["Label"] = labels
    output_file = "labeled_data.csv"
    df.to_csv(output_file, index=False)

# 5. Assess metrics such as precision, recall, and accuracy. How well did our labeller do compared to the input labels we assigned?
def assess_metrics():
    # true positive, true negative, false positive, false negative
    tp = 0
    tn = 0
    fp = 0 
    fn = 0 
    for (idx1, row1), (idx2, row2) in zip(pd.read_csv("labeled_data.csv").iterrows(), pd.read_csv("../test-data/data.csv").iterrows()):
        test_label = row1["Label"]
        actual_label = row2["Class"]
        help = 0

        if test_label == "Potential Misinformation" and actual_label == "Potential Misinformation":
            tp += 1
        elif test_label != "Potential Misinformation" and actual_label != "Potential Misinformation":
            tn += 1
        elif test_label == "Potential Misinformation" and actual_label != "Potential Misinformation":
            # labeler thought it was misinfo when it actually wasn't
            fp += 1
        else:
            # labeler thought it wasn't misinfo but it was
            fn += 1
    print("Precision: ", tp / (tp + fp))
    print("Recall: ", tp / (tp + fn))
    print("Accuracy: ", (tp + tn) / (tp + tn + fp + fn))

if __name__ == "__main__":
    add_relevancies()
    add_toxicity_scores()
    add_misinformation_scores()
    assign_labels()
    assess_metrics()