from scraping.n12_scraper import get_n12_rss_headlines
from scraping.channel14_scraper import get_c14_headlines
from adapters.c14_adapter import main as c14_adapter_main
from analysis.preprocessing import main as preprocess_main
from analysis.group_similar import main as group_similar_main

#get_kan11_rss_headlines()      #doesnt work with rss

if __name__ == "__main__":

    print("-------------- Scraping --------------")
    try:
        get_n12_rss_headlines()
    except Exception as e:
        print(f"Failed to scrape N12: {e}")
    try:
        get_c14_headlines()
    except Exception as e:
        print(f"Failed to scrape Channel 14: {e}")
    print("-------------- Scraping Complete --------------")

    print("-------------- Adapting --------------")
    # Adapters
    try:
        print("Starting Channel14 adapter...")
        c14_adapter_main()
    except Exception as e:
        print(f"Channel14 adapter failed: {e}")
    print("-------------- Adapting Complete --------------")

    print("-------------- Preprocessing --------------")
    try:
        print("Starting preprocessing...")
        preprocess_main()
    except Exception as e:
        print(f"Preprocessing failed: {e}")
    print("-------------- Preprocessing Complete --------------")

    # try:
    #     print("Starting grouping similar articles...")
    #     group_similar_main()
    # except Exception as e:
    #     print(f"Grouping failed: {e}")
    # print("Grouping completed.")





# main flow on terminal:
# python scraping/scrape_all.py         # to scrape all channels    # implement that later
# python analysis/preprocessing.py
# python analysis/group_similar.py
# python analysis/test_group_similar.py
