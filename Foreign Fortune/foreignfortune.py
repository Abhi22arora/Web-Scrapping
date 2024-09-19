import asyncio
import shutil
import tempfile
import json
from parsel import Selector
from typing import List, Dict
from pyppeteer import launch

async def get_page_content(url: str, browser) -> str:
    """Fetch the page content using Pyppeteer."""
    page = await browser.newPage()
    await page.goto(url, {'waitUntil': 'networkidle2'})
    content = await page.content()
    await page.close()
    return content

async def scrape_all_pages(start_url: str, browser) -> List[Dict[str, any]]:
    """Scrape products from all pages of the Foreign Fortune website."""
    all_products = []
    visited_urls = set()
    next_page_url = start_url

    while next_page_url:
        if next_page_url in visited_urls:
            break

        visited_urls.add(next_page_url)
        print(f"Scraping: {next_page_url}")
        html = await get_page_content(next_page_url, browser)
        products = extract_foreignfortune_products(html)
        all_products.extend(products)

        selector = Selector(text=html)
        next_page_elements = selector.css('ul.pagination li a.btn.btn--secondary.btn--narrow')

        next_page_url = None
        for element in next_page_elements:
            svg_icon = element.css('svg.icon-arrow-right')
            if svg_icon:
                parent_div = element.xpath('..')
                if 'btn--disabled' in parent_div.attrib.get('class', ''):
                    print("No more pages to scrape.")
                    return all_products

                next_page_href = element.attrib['href']
                if next_page_href.startswith('/'):
                    next_page_href = next_page_href[1:]
                next_page_url = f"https://foreignfortune.com/{next_page_href}"
                break

        if not next_page_url:
            break

    return all_products

def extract_foreignfortune_products(html: str) -> List[Dict[str, any]]:
    """Extract product details from the Foreign Fortune website."""
    selector = Selector(text=html)
    products = []

    for product in selector.css('.grid__item.grid__item--collection-template.small--one-half.medium-up--one-quarter'):
        title = product.css('a.grid-view-item__link .visually-hidden::text').get()
        price = product.css('.product-price__price::text').get()
        # Extract the image URL
        image_element = product.css('img.grid-view-item__image')
        image_url = image_element.attrib.get('src', '')  # Use the 'src' attribute
        if image_url.startswith('//'):  # Check if it's a relative URL
            image_url = f"https:{image_url}"
        product_data = {
            'title': title,
            'price': price,
            'description': None,
            'image_url': image_url,
        }
        
        products.append(product_data)
    
    return products

async def main():
    start_urls = [
        "https://foreignfortune.com/collections/frontpage",
        "https://foreignfortune.com/collections/shoes",
        "https://foreignfortune.com/collections/foreign-accesories",
        "https://foreignfortune.com/collections/foreign-kids",
        "https://foreignfortune.com/collections/men-unisex",
        "https://foreignfortune.com/collections/women",
        "https://foreignfortune.com/collections/kids",
        "https://foreignfortune.com/collections/coats-hats",
        "https://foreignfortune.com/collections/small-logo-embroidery-t-shirts-1"

    ]

    temp_dir = tempfile.mkdtemp()
    browser = await launch(
        executablePath="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        userDataDir=temp_dir,
        autoClose= False,
    )

    try:
        all_products = []
        for url in start_urls:
            products = await scrape_all_pages(url, browser)
            all_products.extend(products)
            print(f"Total products scraped from {url}: {len(products)}")

        # Write all products to a JSON file at once
        with open('foreignfortune_products.json', 'w', encoding='utf-8') as f:
            json.dump(all_products, f, ensure_ascii=False, indent=4)

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        print("try to close the browser")
        await browser.close()
# Run the scraping task
if __name__ == "__main__":
    asyncio.run(main())
