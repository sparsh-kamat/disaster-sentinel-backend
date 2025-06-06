from serpapi import GoogleSearch

def get_disaster_images(query, num_images=10):

    """
        query format : disaster_type + "in" + disaster_location + "int the year" + "disaster year"
    """
    """Fetches disaster-related image URLs using SerpAPI."""
    
    api_key = "12abaa13b679b1e8be242c795ab06d3c402b700b306004af0c13adb5aab33eea"  # Replace with your SerpAPI key

    params = {
        "q": query,
        "tbm": "isch",  # Image search
        "num": num_images,  # Number of images
        "api_key": api_key
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    image_urls = [img["original"] for img in results.get("images_results", [])[:num_images]]

    return image_urls


if __name__ == "__main__":
    disaster_type = 'storm' ; location = 'chennai' ; state = 'tamil nadu' ; month = 'december' ; year = '2023'
    prompt = f"{disaster_type} disaster in {location}, {state}  during {month} {year} - destruction, damage, rescue operations, and aftermath"
    images = get_disaster_images(prompt)
    print(images)