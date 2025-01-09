from gdeltdoc import GdeltDoc, Filters
import pandas as pd
import time
from flask import Flask, render_template, Response, jsonify
import json
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words
import traceback
import nltk
from newspaper import Article, ArticleException
from newspaper.configuration import Configuration
import requests.exceptions

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


# Download required NLTK data
try:
    print("Init NLTK!")
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('punkt_tab')
except Exception as e:
    print(f"Error downloading NLTK data: {str(e)}")


class ArticleProcessor:
    def __init__(self):
        # Configure newspaper with custom settings
        self.config = Configuration()
        self.config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        self.config.request_timeout = 10  # Reduced timeout
        self.config.number_threads = 1

        # Initialize the summarizer
        self.stemmer = Stemmer('english')
        self.summarizer = LsaSummarizer(self.stemmer)
        self.summarizer.stop_words = get_stop_words('english')

    def fetch_article(self, url):
        try:
            print("Trying to fetch article")
            # Download and parse article
            article = Article(url, config=self.config)
            article.download()
            print("Article downloaded.. Now parsing.. ")
            article.parse()

            # Get article text and create summary
            text = article.text
            if not text:
                return {
                    'error': True,
                    'message': 'No article content found',
                    'title': article.title or 'Article Not Available',
                    'url': url
                }

            summary = self.get_summary(text)

            return {
                'error': False,
                'title': article.title,
                'text': text,
                'summary': summary,
                'authors': article.authors,
                'publish_date': article.publish_date.strftime('%Y-%m-%d') if article.publish_date else None,
                'top_image': article.top_image,
                'url': url
            }
        except ArticleException as e:
            print(f"Article extraction error: {str(e)}")
            return {
                'error': True,
                'message': 'Unable to extract article content',
                'details': str(e),
                'url': url
            }
        except requests.exceptions.Timeout:
            print(f"Timeout error for URL: {url}")
            return {
                'error': True,
                'message': 'The article website took too long to respond',
                'url': url
            }
        except requests.exceptions.RequestException as e:
            print(f"Request error: {str(e)}")
            return {
                'error': True,
                'message': 'Unable to access the article website',
                'url': url
            }
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            print(traceback.format_exc())
            return {
                'error': True,
                'message': 'An unexpected error occurred',
                'url': url
            }

    def get_summary(self, text, sentences_count=5):
        try:
            # Check if text is empty or too short
            if not text or len(text.split()) < 10:
                return "Text is too short to summarize."

            # Create parser
            parser = PlaintextParser.from_string(text, Tokenizer('english'))

            # Generate summary
            summary_sentences = self.summarizer(
                parser.document, sentences_count)

            # Join sentences into a paragraph
            summary = ' '.join([str(sentence)
                               for sentence in summary_sentences])

            # If summary is empty, return first few sentences of text
            if not summary:
                sentences = text.split('.')[:sentences_count]
                summary = '. '.join(sentences) + '@!'

            return summary
        except Exception as e:
            print(f"Error getting summary: {str(e)}")
            return "Unable to generate summary. Using fallback method: " + '. '.join(text.split('.')[:3]) + '.'


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


@app.route("/article/<path:url>")
def get_article_summary(url):
    processor = ArticleProcessor()
    article_data = processor.fetch_article(url)

    if article_data.get('error'):
        # Render error template instead of returning JSON
        return render_template(
            'article_error.html',
            error_message=article_data.get('message'),
            url=article_data.get('url')
        )

    return render_template('article.html', article=article_data)


if __name__ == "__main__":
    app.run(debug=True)
