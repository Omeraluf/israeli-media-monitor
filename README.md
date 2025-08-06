
## Folder structure
israeli-media-monitor/
│
├── scraping/
│   ├── base_scraper.py      # Optional: for shared logic
    ├── kan11_scraper.py
    ├── n12_scraper.py
    ├── reshet13_scraper.py
    └── channel14_scraper.py
│
├── analysis/
│   └── sentiment.py
│
├── main.py
├── requirements.txt
├── .gitignore
└── README.md


## install Requirements
```
pip install -r requirements.txt
```

## activate the environment
```
venv\Scripts\activate
```

## Erase later:

Scraped and structured data from N12 and Channel 14
```
Preprocessed:

Cleaned titles

Normalized dates

Handled bad/missing records

Pushed everything to GitHub

Reviewed the saved JSON (clean and structured)
```