from gdeltdoc import GdeltDoc, Filters
import pandas as pd
import time
from flask import Flask, render_template, Response
import json

app = Flask(__name__)

# Configuration
TIMESPAN = "1d"
BATCH_SIZE = 6
DELAY_SECONDS = 2
SUCCESS_PASS = 0
FAILURE_PASS = 0

# Keyword and Theme Mappings
KEYWORD_MAP = {
    'natural_disasters': [
        'earthquake', 'flood', 'wildfire', 'hurricane', 'typhoon', 'cyclone',
        'landslide', 'drought', 'tsunami', 'volcano', 'tornado', 'avalanche',
        'storm surge', 'heatwave', 'blizzard', 'hailstorm', 'seismic activity',
        'monsoon', 'natural disaster'
    ],
    'conflicts': [
        'war', 'armed conflict', 'civil unrest', 'ethnic violence', 'sectarian violence',
        'uprising', 'rebellion', 'insurgency', 'protest', 'riot', 'terrorism',
        'militant attack', 'genocide', 'occupation', 'siege', 'revolution',
        'guerilla warfare', 'border clash', 'ceasefire violation'
    ],
    'humanitarian': [
        'refugee', 'displacement', 'famine', 'humanitarian crisis', 'epidemic',
        'pandemic', 'cholera outbreak', 'malnutrition', 'aid shortage', 'humanitarian aid',
        'relief efforts', 'asylum seekers', 'migration crisis', 'public health emergency', 'disease outbreak',
        'medical emergency', 'starvation'
    ]
}

THEME_MAP = {
    "natural_disasters": ["NATURAL_DISASTER", "NATURAL_DISASTER_EARTHQUAKE", "NATURAL_DISASTER_FLOOD", "NATURAL_DISASTER_HURRICANE"],
    "conflicts": ["ARMEDCONFLICT", "BLOCKADE", "CEASEFIRE", "MILITARY", "PEACEKEEPING", "RELEASE_HOSTAGE", "SEIGE", "WB_2462_POLITICAL_VIOLENCE_AND_WAR"],
    "humanitarian": ["DISPLACED", "AID_HUMANITARIAN", "EXILE", "REFUGEES", "UNREST_CHECKPOINT", "TAX_DISEASE_EPIDEMIC", "HEALTH_PANDEMIC"]
}


def get_gdelt_data(keywords, theme):
    try:
        f = Filters(
            keyword=keywords,
            timespan=TIMESPAN,
            theme=theme
        )

        gd = GdeltDoc()
        return gd.article_search(f)
    except Exception as e:
        print(f"Error fetching GDELT data: {e}")
        return pd.DataFrame()


def fetch_data_for_category(category):
    keywords = KEYWORD_MAP[category]
    themes = ','.join(THEME_MAP[category])

    all_results = []

    # Process keywords in batches
    for i in range(0, len(keywords), BATCH_SIZE):
        try:
            batch_keywords = keywords[i:i + BATCH_SIZE]
            print("*" * 25)
            print(f"Batch Processing {category}: {batch_keywords}")
            articles_df = get_gdelt_data(batch_keywords, themes)

            if not articles_df.empty:
                # Add category column to the DataFrame
                articles_df['category'] = category

                print(f"Completed batch processing successfully for {
                      category}: {batch_keywords}")
                all_results.append(articles_df)
                global SUCCESS_PASS
                SUCCESS_PASS += 1
            else:
                print(f"No articles found for {category} batch {i}")
                global FAILURE_PASS
                FAILURE_PASS += 1
            time.sleep(DELAY_SECONDS)
        except Exception as e:
            print(f"Error fetching batch {i}: {e}")

    return pd.concat(all_results, ignore_index=True) if all_results else pd.DataFrame()


@app.route("/")
def display_news():
    all_data = {}
    for category in KEYWORD_MAP:
        all_data[category] = fetch_data_for_category(category)

    # Combine all DataFrames (they now include the category column)
    combined_df = pd.concat(all_data.values(), ignore_index=True)

    # Remove duplicate news items based on title (case-insensitive)
    combined_df = combined_df.drop_duplicates(
        subset='title', keep='first', ignore_index=True)
    combined_df['seendate'] = pd.to_datetime(
        combined_df['seendate'], format='%Y%m%dT%H%M%SZ', errors='coerce')
    combined_df = combined_df.sort_values(
        by='seendate', ascending=False).fillna("N/A")

    # Prepare data for the template
    news_items = []
    for index, row in combined_df.iterrows():
        news_items.append({
            'title': row['title'],
            'url': row['url'],
            'url_mobile': row['url_mobile'],
            'seendate': row['seendate'].strftime('%Y-%m-%d %H:%M:%S') if pd.notna(row['seendate']) else "N/A",
            'socialimage': row['socialimage'],
            'domain': row['domain'],
            'language': row['language'],
            'sourcecountry': row['sourcecountry'],
            'category': row['category']  # Add category to news items
        })

    return render_template('news.html', news_items=news_items)


if __name__ == "__main__":
    app.run(debug=True)
