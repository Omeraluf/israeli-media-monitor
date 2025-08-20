from scraping.n12_scraper import get_n12_rss_headlines
from scraping.channel14_scraper import get_c14_headlines
from analysis.preprocessing import main as preprocess_main
from analysis.group_similar import main as group_similar_main

#get_kan11_rss_headlines()      #doesnt work with rss

if __name__ == "__main__":

    try:
        get_n12_rss_headlines()
    except Exception as e:
        print(f"Failed to scrape N12: {e}")
    try:
        get_c14_headlines()
    except Exception as e:
        print(f"Failed to scrape Channel 14: {e}")
    print("Scraping completed.")

    try:
        print("Starting preprocessing...")
        preprocess_main()
    except Exception as e:
        print(f"Preprocessing failed: {e}")
    print("Preprocessing completed.")

    try:
        print("Starting grouping similar articles...")
        group_similar_main()
    except Exception as e:
        print(f"Grouping failed: {e}")
    print("Grouping completed.")





# main flow on terminal:
# python scraping/scrape_all.py         # to scrape all channels    # implement that later
# python analysis/preprocessing.py
# python analysis/group_similar.py
# python analysis/test_group_similar.py
