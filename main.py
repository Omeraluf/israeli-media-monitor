from scraping.kan11_scraper import get_kan11_rss_headlines
from scraping.n12_scraper import get_n12_rss_headlines
from scraping.channel14_scraper import get_c14_headlines

if __name__ == "__main__":
    #get_kan11_rss_headlines()      #doesnt work with rss

    get_n12_rss_headlines()
    get_c14_headlines()
    print("Scraping completed.")

# main flow on terminal:
# python scraping/scrape_all.py         # to scrape all channels    # implement that later
# python analysis/preprocessing.py
# python analysis/group_similar.py
# python analysis/test_group_similar.py
