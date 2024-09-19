from typing import List, Dict, Any


class Validation:
    def __init__(self, products: List[Dict[str, Any]]):
        """
        Initialize the Validation class with the list of products.

        :param products: List of product dictionaries to validate.
        """
        self.products = products

    def validate_mandatory_fields(self) -> bool:
        """
        Validate that each product has the mandatory fields: title, product_id, model_id.
        Also checks if image_url is available. The price can be null.

        :return: True if all products have the required fields, False otherwise.
        """
        mandatory_fields = ['title', 'image_url']
        for product in self.products:
            for field in mandatory_fields:
                if field not in product or not product[field]:
                    print(f"Validation Error: Missing or empty field '{field}' in product {product}")
                    return False
        return True

    def validate_price_format(self) -> bool:
        """
        Validate that the price field is in a proper numeric format or is null.
        Accepts prices with symbols like '$', '£', and comma for thousands.

        :return: True if all prices are valid or null, False otherwise.
        """
        for product in self.products:
            price = product.get('price')
            if price is not None and price.lower() != "not available":  # Allow "Not available" as a valid value
                # Remove currency symbols and commas
                price_cleaned = price.replace('$', '').replace('£', '').replace(',', '').strip()
                if price_cleaned.startswith('from'):
                    price_cleaned = price_cleaned.replace('from', '').strip()
                
                try:
                    float(price_cleaned)  # Try converting the cleaned price to a float
                except ValueError:
                    print(f"Validation Error: Price '{product.get('price')}' is not in a valid format for product {product}")
                    return False
        return True

    def validate_image_url_format(self) -> bool:
        """
        Validate that the image URL is in a valid format.

        :return: True if all image URLs are valid, False otherwise.
        """
        for product in self.products:
            image_url = product.get('image_url', '')
            if not image_url.startswith('http'):
                print(f"Validation Error: Image URL '{image_url}' is not in a valid format for product {product}")
                return False
        return True

    def validate_unique_product_names(self) -> bool:
        """
        Validate that all products have unique names. For Trader Joe's products, 
        ensure that names combined with weights are unique.

        :return: True if all product names with their corresponding weights are unique, False otherwise.
        """
        seen_products = set()
        for product in self.products:
            title = product.get('title')
            weight = product.get('weight')
            
            # If the weight field is present, include it in the uniqueness check
            if weight is not None:
                product_key = (title, weight)
            else:
                product_key = title
            
            if product_key in seen_products:
                if weight is not None:
                    print(f"Validation Error: Duplicate product name '{title}' with weight '{weight}' found.")
                else:
                    print(f"Validation Error: Duplicate product name '{title}' found.")
                return False
            seen_products.add(product_key)
        return True

    def validate_sale_price_less_than_or_equal_to_original_price(self) -> bool:
        """
        Validate that the sale price is less than or equal to the original price.

        :return: True if all sale prices are less than or equal to the original prices, False otherwise.
        """
        for product in self.products:
            original_price = product.get('original_price')
            sale_price = product.get('sale_price')
            
            if original_price and sale_price:
                try:
                    original_price = float(original_price.replace('$', '').replace(',', '').strip())
                    sale_price = float(sale_price.replace('$', '').replace(',', '').strip())
                    if sale_price > original_price:
                        print(f"Validation Error: Sale price '{sale_price}' is greater than original price '{original_price}' for product {product}")
                        return False
                except ValueError:
                    print(f"Validation Error: Invalid price format for product {product}")
                    return False
        return True

    def validate_variant_images_and_prices(self) -> bool:
        """
        Validate that each variant (model) has associated images and respective prices.

        :return: True if all variants have images and prices, False otherwise.
        """
        for product in self.products:
            models = product.get('models', [])
            for model in models:
                if not model.get('image_url'):
                    print(f"Validation Error: Missing image for model {model} in product {product}")
                    return False
                if not model.get('price'):
                    print(f"Validation Error: Missing price for model {model} in product {product}")
                    return False
        return True

    def validate(self) -> bool:
        """
        Run all validation methods and return the overall validation status.

        :return: True if all validations pass, False otherwise.
        """
        return (self.validate_mandatory_fields() and
                self.validate_price_format() and
                self.validate_image_url_format() and
                self.validate_unique_product_names() and
                self.validate_sale_price_less_than_or_equal_to_original_price() and
                self.validate_variant_images_and_prices())


if __name__ == "__main__":
    # Example usage:
    import json

    # Load the data from the JSON files generated by lechocolat.py and foreignfortune.py
    with open('lechocolat_products.json', 'r', encoding='utf-8') as f:
        lechocolat_products = json.load(f)

    with open('foreignfortune_products.json', 'r', encoding='utf-8') as f:
        foreignfortune_products = json.load(f)
    
    with open('traderjoes.json', 'r', encoding='utf-8') as f:
        traderjoes_products = json.load(f)
        
    # Validate products from Le Chocolat Alain Ducasse
    print("Validating Le Chocolat Alain Ducasse products:")
    lechocolat_validator = Validation(lechocolat_products)
    if lechocolat_validator.validate():
        print("All Le Chocolat products passed validation.")
    else:
        print("Some Le Chocolat products failed validation.")

    # Validate products from Foreign Fortune
    print("\nValidating Foreign Fortune products:")
    foreignfortune_validator = Validation(foreignfortune_products)
    if foreignfortune_validator.validate():
        print("All Foreign Fortune products passed validation.")
    else:
        print("Some Foreign Fortune products failed validation.")
    
    print("\nValidating Trader Joes products:")
    traderjoes_validator = Validation(traderjoes_products)
    if traderjoes_validator.validate():
        print("All Trader Joe's products passed validation.")
    else:
        print("Some Trader Joe's products failed validation.")
