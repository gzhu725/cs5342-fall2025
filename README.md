# CS5432 Homework 3 
### Group 6: Xueyi He, Yufan Peng, Boshen Yuan, Gloria Zhu

## File Structure

The file structure is as follows.
```.
├── assign3/
│   ├── labeler-inputs/
│   │   ├── data_scraper.py
│   │   ├── input-data-keywords.csv
│   │   └── raw_scraped.csv
│   ├── pylabel/
│   │   ├── .env-TEMPLATE
│   │   ├── labeled_data.csv
│   │   └── policy_proposal_labeler.py
│   └── test-data/
│       └── data.csv
└── README.md
```

## Folder Descriptions
- `assign3`: root directory which contains the directories discussed below.
    - `labeler-inputs`: directory where all scripts and csvs regarding Bluesky post scraping occurs. 
        - `input-data-keywords.csv`: several keywords used to scrape posts on Bluesky that have these keywords within the post. 
        - `data_scraper.py`: a script that scrapes for posts off of Bluesky for each keyword in the `input-data-keywords.csv` file. It will also ensure for relevancy, making sure that transgender related terms are included within the post. The results will save in a new csv called `raw_scraped.csv`. 
        - `raw_scraped.csv`: generated csv file after running `data_scraper.py`
    - `pylabel`: directoy responsible for our labeler.
        - `.env-TEMPLATE`: template to help you construct a `.env` file in the same folder.
        - `labeled_data.csv`: the results of running our labeler on our tests posts.
        - `policy_proposal_labeler.py`: script for our labeler.
    - `test-data`: directory where `data.csv`, the test data, lives.
        - `data.csv`: Original file with all our classifications for input posts, based on our rubric.

## Test
- To run all scripts, please ensure you have a `.env` file in `pylabel/` with the appropriate information listed in `pylabel/.env-TEMPLATE` and install all dependencies with 

```
pip install pandas python-dotenv atproto requests groq
```

- To run the data scraper in `labeler-inputs/`, run 
```
python data_scraper.py
```
This should get all relevant posts and save them in `raw_scraped.csv`. 
- To run the labeler, run 
```
python policy_proposal_labeler.py
``` 
located in `pylabel/`. The new data will be saved in `labeled_data.csv`.

## Output Meaning
For the labeler, the output labels will all be part of `pylabel/labeled_data.csv`. Each column in the  is as follows: Original Text of the post, Is Related (0 if post is unrelated to transgender issues, 1 otherwise), Toxicity (toxicity score provided by Perspective API from 0-1), Misinformation (Score of 0-3 given from LLaMA LLM), Label (Potential misinformation or not detected),Post Link, Class (actual classification analyzed by us),Post Type (real or generated). 

To check the label given by the labeler, use the Label column. To check the actual label assessed by us, use the Class column.

The precision, recall, and accuracy are also all calculated and printed to the console.