import asyncio
import shutil
import os
import json
import tempfile
from parsel import Selector
from typing import List, Dict
from pyppeteer import launch

async def get_page_content(url: str, browser) -> str:
    """Fetch the page content using Pyppeteer."""
    page = await browser.newPage()
    await page.goto(url, {'waitUntil': 'networkidle2'})
   
    content = await page.content()
    #print(content)
    await page.close()
    return content

def extract_lechocolat_products(html: str) -> List[Dict[str, any]]:
    """Extract product details from the Le Chocolat Alain Ducasse website."""
    selector = Selector(text=html)
    products = []

    # Using the appropriate selector to find each product element
    product_elements = selector.css('.productMiniature')  # Update to match the actual class name

    if not product_elements:
        print("No product elements found using the '.productMiniature' selector.")
        return products

    for product in product_elements:
        # Extract the product name
        title = product.css('h2.productMiniature__title::text').get(default='').strip()

        # Extract the description - combining subtitle and weight if available
        subtitle = product.css('h3.productMiniature__subtitle::text').get(default='').strip()
        weight = product.css('.productMiniature__weight::text').get(default='').strip()
        description = f"{subtitle} {weight}".strip()

        # Extract the price
        price = product.css('span.productMiniature__price::text').get(default='').strip()
        
        # Extract the image URL using the src attribute
        image_element = product.css('img')
        image_url = image_element.attrib.get('src', '')  # Use the 'src' attribute for the main image
        if image_url.startswith('//'):  # Check if it's a relative URL
            image_url = f"https:{image_url}"

        # Constructing the product data dictionary
        product_data = {
            'title': title,
            'price': price,
            'description': description,
            'image_url': image_url
        }
        
        products.append(product_data)
    
    return products


async def scrape_pages(urls: List[str]) -> List[Dict[str, any]]:
    """Scrape products from the provided URLs of the Le Chocolat Alain Ducasse website."""
    all_products = []

    temp_dir = tempfile.mkdtemp()
    browser = await launch(
        executablePath="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        userDataDir=temp_dir,
        autoClose= False
    )

    try:
        for url in urls:
            print(f"Scraping: {url}")
            html = await get_page_content(url, browser)
            products = extract_lechocolat_products(html)
            if not products:
                print(f"No products found on {url}")
            all_products.extend(products)

    finally:
        try:
            await browser.close()
        except Exception as e:
            print(f"Error closing browser: {e}")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    return all_products

async def main():
    urls = [
        "https://www.lechocolat-alainducasse.com/uk/chocolates",
        "https://www.lechocolat-alainducasse.com/uk/chocolate-bar",
        "https://www.lechocolat-alainducasse.com/uk/breakfast-snacks",
        "https://www.lechocolat-alainducasse.com/uk/simple-pleasures",
        "https://www.lechocolat-alainducasse.com/uk/chocolate-gift",
        "https://www.lechocolat-alainducasse.com/uk/specialty-coffee-beans",
        "https://www.lechocolat-alainducasse.com/uk/specialty-coffee-capsules",
    ]
    
    all_products = await scrape_pages(urls)
    
    with open('lechocolat_products.json', 'w',encoding='utf-8') as f:
        json.dump(all_products, f, indent=4,ensure_ascii=False)
    
    print(f"Total products scraped: {len(all_products)}")

# Run the scraping task
if __name__ == "__main__":
    asyncio.run(main())
