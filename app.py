import os
import requests
from bs4 import BeautifulSoup

session = requests.Session()
def sign_in(matric_no, password):
    print("============================== Result checker =============================")
    base_name = 'https://portal.unaab.edu.ng'
    login_url = base_name + "/Login.aspx"
    # Gets  required payload from the login page
    login_page = session.get(login_url)
    login_page.raise_for_status()  # Check for HTTP errors
    soup = BeautifulSoup(login_page.text, 'html.parser') # extract login payload
    viewstate = soup.find('input', {'name': '__VIEWSTATE'})['value']
    viewstategenerator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})['value']
    eventvalidation = soup.find('input', {'name': '__EVENTVALIDATION'})['value']
    payload = {
        "__VIEWSTATE": viewstate,
        "__VIEWSTATEGENERATOR": viewstategenerator,
        "__EVENTVALIDATION": eventvalidation,
        "ctl00$ctl00$ContentPlaceHolder1$centerpane$UserName": matric_no,
        "ctl00$ctl00$ContentPlaceHolder1$centerpane$Password": password,
        "ctl00$ctl00$ContentPlaceHolder1$centerpane$Button1": "Log In"
    }

    # Login to the portal
    login_response = session.post(login_url, data=payload, allow_redirects=True)
    login_response.raise_for_status()  # Check for HTTP errors
    # Check if login was successful
    if login_response.url != login_url:
        return (login_response)
    return None

def get_result(level, semester, login_response):
    base_name = 'https://portal.unaab.edu.ng'
    # Fetch the result page
    soup = BeautifulSoup(login_response.text, 'html.parser')
    # Find the link to the download result page
    result_text = soup.find('a', string='Result')
    if result_text:
        result_link = base_name + result_text['href']
        results_response = session.get(result_link)
        results_response.raise_for_status()  # Check for HTTP errors
        results_soup = BeautifulSoup(results_response.text, 'html.parser')
        match_found = False
        for row in results_soup.find_all('tr'):
            columns = row.find_all('td')
            if len(columns) >= 4:
                doc_level = columns[2].text.strip()
                doc_semester = columns[1].text.strip().lower()
                if f"{level} Level" == doc_level and semester.lower() == doc_semester:
                    result_url = base_name + "/Secure/" + columns[3].find('a')['href']
                    result_pdf_response = session.get(result_url)
                    result_pdf_response.raise_for_status()  # Check for HTTP errors
                    return result_pdf_response.content
        err_msg = f"No result found for {level} level and {semester} semester"
    else:
        err_msg = 'Result link not found'
    raise LookupError(err_msg)