import re
from bs4 import BeautifulSoup
import requests

def clean_text(text: str) -> str:
    # Step 1: Remove leading/trailing whitespace from each line and drop fully blank lines
    cleaned_lines = [line.strip() for line in text.splitlines()]
    cleaned_text = "\n".join(cleaned_lines)
    
    # Step 2: Collapse multiple consecutive empty lines into a single one
    cleaned_text = re.sub(r'\n\s*\n+', '\n\n', cleaned_text)
    
    return cleaned_text.strip()

# Fetch and parse
html_doc = requests.get("https://en.wikipedia.org/wiki/Marvel_Cinematic_Universe").text
soup = BeautifulSoup(html_doc, "lxml")


# Extract and clean text
raw_text = soup.get_text()
final_text = clean_text(raw_text)

# print(final_text)

with open("cleaned.txt", "w", encoding="utf-8") as file:
    file.write(final_text)
