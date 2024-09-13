import json
import os

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

for gpn in gpns:
    path = f"../data/audio/input/{gpn}"
    if not os.path.exists(path):
        os.makedirs(path)

talks = {}
for index, conference_link in enumerate(conferences_links):
    conference_soup = BeautifulSoup(
        requests.get(BASE_URL + conference_link).content, "html.parser"
    )
    talk_elements = conference_soup.find_all("h3")
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

        description = talk_soup.find("p", class_="description").text.replace("\n", "")

        metadata = {
            "title": title,
            "gpn": gpns[index],
            "speakers": speakers,
            "duration": duration,
            "date": date,
            "description": description,
        }

        with open(
            f"../data/audio/input/{gpns[index]}/{title}_metadata.json", mode="w"
        ) as file:
            file.write(json.dumps(metadata, indent=4))

        # Download and write mp3
        download_tag = talk_soup.find("div", class_="row audio").find(
            "div", string="Download mp3"
        )
        download_link = download_tag.parent["href"]
        response = requests.get(download_link, stream=True)
        with open(f"../data/audio/input/{gpns[index]}/{title}.mp3", mode="wb") as file:
            for chunk in response.iter_content(chunk_size=10 * 1024):
                file.write(chunk)
