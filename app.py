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
    'water_disaster': ['flood', 'flash flood', 'storm surge', 'tsunami', 'monsoon'],
    'storm_disaster': ['hurricane', 'typhoon', 'cyclone', 'tornado', 'windstorm', 'sandstorm'],
    'geological_diaster': ['earthquake', 'seismic activity', 'volcano', 'lava flow', 'landslide'],
    'extreme_weather': ['drought', 'heatwave', 'blizzard', 'hailstorm', 'cold wave', 'wildfire'],
}

THEME_MAP = {
    "water_disaster": ["NATURAL_DISASTER_FLOOD", "NATURAL_DISASTER_WIND_STORMS", "NATURAL_DISASTER_MONSOON", "NATURAL_DISASTER_TSUNAMI"],
    "storm_disaster": ["NATURAL_DISASTER_HURRICANE", "NATURAL_DISASTER_TYPHOON", "NATURAL_DISASTER_CYCLONE", "NATURAL_DISASTER_TORNADO", "NATURAL_DISASTER_WINDSTORM"],
    "geological_diaster": ["NATURAL_DISASTER_EARTHQUAKE", "NATURAL_DISASTER_VOLCANO", "NATURAL_DISASTER_LAVA", "NATURAL_DISASTER_LANDSLIDE"],
    "extreme_weather": ["NATURAL_DISASTER_DROUGHT", "NATURAL_DISASTER_HEATWAVE", "NATURAL_DISASTER_BLIZZARD", "NATURAL_DISASTER_WILDFIRE"],    
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
    return render_template('news.html')

@app.route("/get_news")
def get_news():
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

    return Response(json.dumps(news_items), mimetype='application/json')


if __name__ == "__main__":
    app.run(debug=True)
