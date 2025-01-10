# Disaster Alert Monitor    
 
A Flask-based web application that monitors and visualizes real-time disaster alerts using the [GDELT 2.0 Doc API](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/).  
The application aggregates and categorizes natural disaster news to support immediate humanitarian response efforts.  
🌎 Live: https://gdelt-news-alert.onrender.com   
  
![globalalert](https://github.com/user-attachments/assets/b032ed5d-511a-4d79-9aa0-b31f2538106d)  
  
  
## Overview

This application serves as a disaster monitoring tool, specifically designed to track:  
- Water-related disasters (floods, tsunamis)
- Storm events (hurricanes, cyclones)
- Geological events (earthquakes, landslides)
- Extreme weather conditions
  
  
![globalalert32](https://github.com/user-attachments/assets/1565ccaa-1b6b-406b-a0b6-89e7fead98f1)  
  
  
Built on top of the [GDELT 2.0 Python API Client](https://github.com/alex9smith/gdelt-doc-api), it provides a real-time dashboard for monitoring global disaster events.
  
## Features

- Real-time disaster news monitoring and categorization
- Interactive dashboard with category-based filtering
- Article summarization capabilities
- Cached responses for improved performance
- Statistical overview of disaster categories

## Installation

1. Clone the repository:
```bash
git clone https://github.com/nuhman/gdelt-news-alert.git
cd gdelt-news-alert
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the Flask server:
```bash
python app.py
```

2. Access the application at `http://localhost:5000`

## Dependencies

- Flask
- newspaper3k
- GDELT DOC API Client (Added as part of the repository)  
- sumy
- nltk


## Technical Details

- Article summarization is performed locally using the `sumy` library
- News data is cached client-side for 5 minutes to optimize performance
- Real-time data fetching with automatic refresh capabilities





