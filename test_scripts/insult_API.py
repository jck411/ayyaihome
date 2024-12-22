import requests

def get_insult():
    """
    Fetch a random insult from the Evil Insult API.

    Returns:
        str: The generated insult, or an error message if the API call fails.
    """
    # API URL
    url = "https://evilinsult.com/generate_insult.php"
    
    # Query parameters
    params = {
        "lang": "en",  # Language: English
        "type": "json"  # Response format: JSON
    }
    
    try:
        # Make the API request
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an error for HTTP errors
        
        # Parse the JSON response
        data = response.json()
        return data.get("insult", "No insult found.")  # Get the insult or default message if missing
    
    except requests.exceptions.RequestException as e:
        # Handle any HTTP or connection errors
        return f"Error fetching insult: {e}"
    except ValueError:
        # Handle JSON parsing errors
        return "Error: Unable to parse the response."

# Example usage
if __name__ == "__main__":
    insult = get_insult()
    print(f"Generated Insult: {insult}")
