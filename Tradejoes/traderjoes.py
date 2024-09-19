import asyncio
import json
import tempfile
from typing import List, Dict
from parsel import Selector
from pyppeteer import launch

async def get_page_content(url: str, browser) -> str:
    """Fetch the page content using Pyppeteer."""
    page = await browser.newPage()
    await page.goto(url, {'waitUntil': 'networkidle2'})
    await page.waitForSelector('li.ProductList_productList__item__1EIvq', {'timeout': 10000})
    content = await page.content()
    await page.close()
    return content

async def scrape_all_pages(start_url: str, browser) -> List[Dict[str, any]]:
    """Scrape products from all pages of the Trader Joe's website."""
    all_products = []
    next_page_button_selector = '.Pagination_pagination__arrow__3TJf0.Pagination_pagination__arrow_side_right__9YUGr'

    page = await browser.newPage()
    
    # Maximize the viewport size for better scraping
    await page.setViewport({'width': 1920, 'height': 1080})
    
    await page.goto(start_url, {'waitUntil': 'networkidle2'})
    await page.waitForSelector('li.ProductList_productList__item__1EIvq', {'timeout': 10000})

    page_number = 1
    while True:
        print(f"Scraping page {page_number}...")

        # Scroll the page to load all products
        last_height = await page.evaluate('document.body.scrollHeight')
        while True:
            print("Scrolling to load more products...")
            await page.evaluate("window.scrollBy(0, document.body.scrollHeight);")
            await asyncio.sleep(3)  # Adjust sleep time if necessary
            new_height = await page.evaluate('document.body.scrollHeight')
            if new_height == last_height:
                break
            last_height = new_height

        html = await page.content()
        if not html:
            print(f"No content found on page {page_number}.")
            break

        products = extract_traderjoes_products(html)
        if not products:
            print(f"No products found on page {page_number}.")
            break

        all_products.extend(products)
        print(f"Scraped {len(products)} products from page {page_number}.")

        # Check for the next page button using the class-based selector
        next_button = await page.querySelector(next_page_button_selector)

        # Additional check to avoid infinite loop
        if not next_button or await page.evaluate('(el) => el.disabled', next_button):
            print("No more pages to scrape or next button is disabled.")
            break

        try:
            await next_button.click()
            await page.waitForNavigation({'waitUntil': 'networkidle2'})  # Wait for the next page to load fully
            await page.waitForSelector('li.ProductList_productList__item__1EIvq', {'timeout': 10000})
            page_number += 1
        except Exception as e:
            print(f"Error clicking next button: {e}")
            break

    await page.close()
    return all_products

def extract_traderjoes_products(html: str) -> List[Dict[str, any]]:
    """Extract product details from the Trader Joe's website."""
    selector = Selector(text=html)
    products = []

    base_url = "https://www.traderjoes.com"

    for product in selector.css('li.ProductList_productList__item__1EIvq'):
        title = product.css('a.ProductCard_card__title__301JH::text').get()
        price = product.css('span.ProductPrice_productPrice__price__3-50j::text').get()
        weight = product.css('span.ProductPrice_productPrice__unit__2jvkA::text').get()
        
        # Check for price absence and look for alternative text
        if not price:
            price = product.css('span.ProductPrice_productPrice__noPriceText__Is9Tc::text').get()
        
        # Extract the image URL
        image_element = product.css('img.ProductCard_card__cover__19-g3')
        image_url = image_element.attrib.get('src', '')

        if image_url.startswith('/'):  # Convert relative URL to absolute
            image_url = f"{base_url}{image_url}"
        
        product_data = {
            'title': title,
            'price': price,
            'weight': weight,
            'image_url': image_url,
        }
        
        products.append(product_data)
    
    return products


async def main():
    start_urls = [
        "https://www.traderjoes.com/home/products/category/food-8",
        "https://www.traderjoes.com/home/products/category/beverages-182",
        "https://www.traderjoes.com/home/products/category/flowers-plants-203",
        "https://www.traderjoes.com/home/products/category/everything-else-215"
        # Add more URLs as needed
    ]

    temp_dir = tempfile.mkdtemp()
    browser = await launch(
        executablePath="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        userDataDir=temp_dir,
        autoClose=False,
#        headless=False,
        args=['--start-maximized']  # Maximize the browser window
    )

    try:
        all_products = []
        for url in start_urls:
            print(f"Starting scraping for URL: {url}")
            products = await scrape_all_pages(url, browser)
            all_products.extend(products)
            print(f"Total products scraped from {url}: {len(products)}")

        # Write all products to a JSON file at once
        with open('traderjoes.json', 'w', encoding='utf-8') as f:
            json.dump(all_products, f, ensure_ascii=False, indent=4)

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        print("Trying to close the browser")
        await browser.close()

# Run the scraping task
if __name__ == "__main__":
    asyncio.run(main())
