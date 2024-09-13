import requests
from bs4 import BeautifulSoup

BASE_URL = "https://media.ccc.de"
CONFERENCES_URL = f"{BASE_URL}/b/conferences/gpn"

conferences_soup = BeautifulSoup(requests.get(CONFERENCES_URL).content, "html.parser")
conferences = conferences_soup.find_all("a", class_="thumbnail conference")
conferences_links = []
gpns = []
for conference in conferences:
    conference_link = conference["href"]
    conferences_links.append(conference_link)
    # Get conference years
    gpn = conference_link.split("/")[-1]
    gpns.append(gpn)

talks = {}
for index, conference_link in enumerate(conferences_links):
    conference_soup = BeautifulSoup(
        requests.get(BASE_URL + conference_link).content, "html.parser"
    )
    talk_elements = conference_soup.find_all("h3")
    talks = {}
    for talk in talk_elements:
        talk_link = talk.find("a")
        talks[talk_link.text.replace("\n", "")] = {
            "gpn": gpns[index],
            "link": talk_link["href"],
        }

    print(talks)
