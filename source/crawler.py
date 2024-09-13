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
        link = talk.find("a")
        title = link.text.replace("\n", "")

        talk_soup = BeautifulSoup(
            requests.get(BASE_URL + link["href"]).content, "html.parser"
        )
        speaker_paragraphs = talk_soup.find("p", class_="persons").find_all("a")
        speakers = []
        for speaker in speaker_paragraphs:
            speakers.append(speaker.text.replace("\n", ""))

        metadata_list = talk_soup.find("ul", class_="metadata")
        metadata = metadata_list.find_all("li")
        duration = metadata[0].text.replace("\n", "")
        date = metadata[1].text.replace("\n", "")

        talks[title] = {
            "title": title,
            "gpn": gpns[index],
            "speakers": speakers,
            "duration": duration,
            "date": date,
        }
