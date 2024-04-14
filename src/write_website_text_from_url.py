'''
Author: Logan Maupin
Date: 09/17/2023

This python script is a collection of functions used to extract body
text from a given url and write it to a text file. The text file can
be written to from multiple websites. 
'''
import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse


def get_current_date_string() -> str:
    '''
    This function gets the current date string in mm/dd/yyyy format

    Returns: date string in mm/dd/yyyy format
    '''
    # Get the current date and time
    current_datetime = datetime.now()
    
    # Format the date as a string (e.g., "MM-DD-YYYY")
    date_string = current_datetime.strftime("%m-%d-%Y")
    
    return date_string


def is_website_up(url: str) -> bool:
    '''
    This function pings the url's server to see if 
    the website is up and running.

    Parameters: 
    url: any website url string you wish to test like google.com

    Return: Bool - True if the website is up and running.
    '''
    response = requests.get(url)
    return response.status_code == 200


def extract_domain_from_website(url: str) -> str or None:
    '''
    This function will take a given url like www.google.com for example

    Parameters: 
    url: the string of the url name you wish to pass in like 'google.com'

    Return: str of website host name like google.com
    '''

    website_is_up = is_website_up(url)
    if website_is_up:
        parsed_url = urlparse(url=url)
        if parsed_url:
            return parsed_url.hostname

        else:
            print("Website name not found.")


def remove_excess_whitespace(text_to_process: str) -> str:
    '''
    This function removes excess whitespace and needless blank lines
    given some input text. It will return an output text string that 
    is cleaned up.

    Parameters: 
    text_to_process: input_string to clean up like 'example\n\n\n'

    Returns: output string without excess whitespace or blank lines.
    '''
    cleaned_text = "\n".join(line.strip() for line in text_to_process.splitlines() if line.strip())
    return cleaned_text


def extract_website_text(url: str) -> str:
    '''
    This function extracts the text from the given url using 
    the requests and beautiful soup library. 

    Parameters:
    url: string of url name like google.com for example

    Return: string of text from the url
    '''
    website_is_up = is_website_up(url)
    if website_is_up:

        # Send an HTTP GET request to the URL
        response = requests.get(url)

         # Parse the HTML content of the page using BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

           # Find all <p> (paragraph) tags in the HTML
        paragraph_tags = soup.find_all("p")
        
        # Extract the text from the paragraph tags and join them into one string
        extracted_text = "\n".join(tag.get_text(strip=True) for tag in paragraph_tags)        
        

        return remove_excess_whitespace(extracted_text)



def build_header_string(url: str) -> str or None:
    '''
    This function takes the url and extracts the domain name from it,
    i.e. google.com into Google, then it will add that to a formatted
    header text string to add to the top of each file entry. 

    Parameters:
    url: any url string like 'google.com' for example.

    Return: header string to add to the top of a 
    text file with the domain name.
    '''
    website_is_up = is_website_up(url)
    if not website_is_up:
        return None
    
    website_name = extract_domain_from_website(url)
    if website_name:
        header_string_start = '-'*25 + '\n'
        output_string = header_string_start + \
        f'The following information is from {url}' + \
        '\n' + header_string_start + "\n"
        return output_string
    

def user_input_txt_filename() -> str or None:
    '''
    This function is a while loop that asks the user whether or not
    they wish to provide their own filename to write to or not.

    Return: filename or None if no.
    '''
    while True:

        # ask the user if they wish to provide a filename or not:
        custom_filename_input = input("Do you wish to use a custom filename to write to? (y/n): ").lower()
        if custom_filename_input not in ['y', 'n']:
            continue

        elif custom_filename_input == 'y':
            custom_filename = input("Please input the filename you wish to use: ").strip()
            
            if '.txt' in custom_filename.lower():
                return custom_filename
            
            else: 
                custom_filename += '.txt'
                return custom_filename
        
        elif custom_filename_input == 'n':
            return None


def write_text_to_file(text_to_write: str, text_filename: str, url: str) -> None:
    '''
    This function just writes what text you want to the text file.
    Specifically it appends the text rather than overwriting the file.

    Parameters: 
    text_to_write: string of what text you want to write to the file
    text_filename: string of what the text filename will be. like example.txt
    url: string of url name you wish to write about like google.com

    Return: None
    '''
    header_text = build_header_string(url)
    # Create or open a text file and save the extracted text to it
    with open(text_filename, "a", encoding="utf-8") as text_file:
        text_file.write(header_text)
        text_file.write(text_to_write)
        print(f"Text extracted and saved to {text_filename}")


def write_text_to_txt_file_from_url(url: str) -> None:
    '''
    This is an alternative function you can use which will write the 
    text from the url's </p> tags but using passed in url arguments
    instead of user input. Better if you need to do this for a long list
    of articles instead of one at a time. 
    
    Returns: txt file name if it properly saved.
    '''
    website_name = extract_domain_from_website(url=url)
    website_body_text = extract_website_text(url)
    text_filename = f'{website_name}.txt'
    write_text_to_file(website_body_text, text_filename, url)

    if os.path.exists(text_filename):
        return text_filename


def main():
    '''
    This function defines the order in which to use all the functions
    as an example of how one would get the text and write it to a file.

    Return: None
    '''
    # First let's define what our url will be, so we'll ask the user for it.
    url = input('Please input the website url you wish to extract text from: \n')

    # Extract the company name / url domain name from the website
    # like Google from google.com for example
    website_name = extract_domain_from_website(url)

    website_body_text = extract_website_text(url)

    text_filename = user_input_txt_filename()

    if not text_filename:

        text_filename = f'{website_name}.txt'

    write_text_to_file(website_body_text, text_filename, url)


if __name__ == "__main__":
    main()
    