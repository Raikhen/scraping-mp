import requests
import pandas   as pd
from bs4        import BeautifulSoup

def get_yds_grades():
    # Get that sweet soup
    url     = 'https://www.mountainproject.com/international-climbing-grades'
    content = requests.get(url).content
    soup    = BeautifulSoup(content, features = 'html.parser')

    # Get the list
    main    = soup.find(class_ = 'col-md-6')
    table   = main.find('table')
    df      = pd.read_html(str(table))[0]
    as_list = list(df['YDS USA'])[:-1]

    # Convert to dictionary
    grades = {}

    for i, grade in enumerate(as_list):
        grades[grade] = i

    return grades

print(get_yds_grades())
