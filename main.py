#!/usr/bin/python3

from typing import List
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import json

WEBSITE_NAME = ""  # ENTER YOUR WEBSITE NAME IN HERE
OUT_FILE = "./out.json"
PAGE_LEN = 20  # ENTER THE NUMBER OF PAGES IN YOUR ALL SECTION OF YOUR WEBSITE HERE


options = Options()
options.headless = True
options.add_argument("--window-size=1920,1080")
driver = Chrome(options=options)


def normalize_contents(p_nodes: List[str]) -> str:
    paragraphs = ""
    raw_paragraphs = "\n".join([node.text for node in p_nodes])
    unicode_split = raw_paragraphs.split(r"\u")
    for i, string in enumerate(unicode_split):
        if i == 0:
            pass
        elif len(string) > 4:
            string.replace(string[:4], chr(int(string[:4]), 16))
        else:
            continue
        paragraphs += string
    paragraphs.replace(r"\n", "\n")
    return paragraphs


def scrape_article_contents(url: str) -> str:
    print(url)
    driver.get(url)
    raw_paragraphs = driver.find_element(By.CLASS_NAME, "entry-content").find_elements(
        By.TAG_NAME, "p"
    )
    return normalize_contents(raw_paragraphs[1:]) if len(raw_paragraphs) >= 1 else ""


def scrape_page(url: str) -> List[dict]:
    articles = []
    print(url)
    driver.get(url)
    continue_reading = []
    for i, entry in enumerate(reversed(driver.find_elements(By.TAG_NAME, "article"))):
        entry_content = entry.find_element(By.CLASS_NAME, "entry-content")
        p_nodes = entry_content.find_elements(By.TAG_NAME, "p")
        author = ""
        if len(p_nodes) >= 1:
            author = p_nodes[0].text[3:]
        entry_title = entry.find_element(By.CLASS_NAME, "entry-title").find_element(
            By.TAG_NAME, "a"
        )
        entry_footer = entry.find_element(By.CLASS_NAME, "entry-footer")
        entry_image = entry_content.find_elements(By.CLASS_NAME, "wp-block-image")
        posted_on = entry_footer.find_element(By.CLASS_NAME, "posted-on")
        categories = []
        for raw_cat in entry_footer.find_element(
            By.CLASS_NAME, "cat-links"
        ).find_elements(By.TAG_NAME, "a"):
            categories.append(raw_cat.text)
        image_url = ""
        image_caption = ""
        if len(entry_image) >= 1:
            image_url = entry_image[0].get_attribute("href")
            image_caption_el = entry_image[0].find_elements(By.TAG_NAME, "figcaption")
            if len(image_caption_el) >= 1:
                image_caption = image_caption_el[0].text
        article = {
            "url": entry_title.get_attribute("href"),
            "title": entry_title.text,  # may be wrong
            "published": posted_on.find_element(
                By.CLASS_NAME, "published"
            ).get_attribute("datetime"),
            "updated": posted_on.find_element(By.CLASS_NAME, "updated").get_attribute(
                "datetime"
            ),
            "categories": categories,
        }
        if author != "":
            article["author"] = author
        if image_url != "":
            article["image_url"] = image_url
        if image_caption != "":
            article["image_caption"] = image_caption
        paragraphs = ""
        more_links = entry_content.find_elements(By.CLASS_NAME, "more-link")
        if len(more_links) > 0:
            continue_reading.append((i, more_links[0].get_attribute("href")))
        elif len(p_nodes) >= 1:
            paragraphs = normalize_contents(p_nodes[1:])
        if paragraphs != "":
            article["paragraphs"] = paragraphs
        articles.append(article)
    for index, href in continue_reading:
        articles[index]["paragraphs"] = scrape_article_contents(href)
    return articles


out = []

for i in reversed(range(1, PAGE_LEN + 1)):
    out.extend(scrape_page(f"https://{WEBSITE_NAME}.wordpress.com/page/" + str(i)))

print(json.dumps(out, sort_keys=False, indent=4))
