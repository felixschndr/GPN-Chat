import json
from html import unescape

import requests
from bs4 import BeautifulSoup, ResultSet

from source.logger import LoggerMixin


class Crawler(LoggerMixin):
    def __init__(self):
        super().__init__()
        self.BASE_URL = "https://media.ccc.de"
        self.CONFERENCES_URL = f"{self.BASE_URL}/b/conferences/gpn"
        self.conferences_links = []
        self.gpns = []
        self.talks = {}

    def run(self) -> None:
        self.get_conferences()
        self.get_talks()

    def get_conferences(self) -> None:
        conferences_page = requests.get(self.CONFERENCES_URL).content

        conferences_soup = BeautifulSoup(conferences_page, "html.parser")
        conferences = conferences_soup.find_all("a", class_="thumbnail conference")
        for conference in conferences:
            link = conference["href"]
            self.conferences_links.append(link)
            # Get conference years
            gpn = link.split("/")[-1]
            self.gpns.append(gpn)

    def get_talks(self) -> None:
        for index, conference_link in enumerate(self.conferences_links):
            conference_site = requests.get(self.BASE_URL + conference_link).content
            conference_soup = BeautifulSoup(conference_site, "html.parser")
            talk_elements = conference_soup.find_all("h3")
            self.create_metadata_for_talks(talk_elements, index)

    def create_metadata_for_talks(
        self, talks: list[ResultSet], conference_index: int
    ) -> None:
        for talk in talks:
            link = talk.find("a")
            title = link.text.replace("\n", "")

            self.log.debug(f"Creating metadata file for {title}")

            talk_site = requests.get(self.BASE_URL + link["href"]).content
            self.talk_soup = BeautifulSoup(talk_site, "html.parser")
            speaker_paragraphs = self.talk_soup.find("p", class_="persons").find_all(
                "a"
            )
            speakers = []
            for speaker in speaker_paragraphs:
                speakers.append(speaker.text.replace("\n", ""))

            metadata_list = self.talk_soup.find("ul", class_="metadata")
            metadata = metadata_list.find_all("li")
            duration = metadata[0].text.replace("\n", "")
            date = metadata[1].text.replace("\n", "")

            description_paragraph = self.talk_soup.find("p", class_="description")
            description = (
                description_paragraph.text.replace("\n", "")
                if description_paragraph
                else ""
            )
            description = unescape(description)

            metadata = {
                "title": title,
                "gpn": self.gpns[conference_index],
                "speakers": speakers,
                "duration": duration,
                "date": date,
                "description": description,
            }

            self.write_metadata_of_talk(metadata)
            self.download_audio_of_talk(metadata)

    @staticmethod
    def write_metadata_of_talk(metadata: dict) -> None:
        with open(
            f"../data/metadata/{metadata.title.replace('/', ' ')}.json",
            mode="w",
            encoding="utf-8",
        ) as file:
            file.write(json.dumps(metadata, indent=4, ensure_ascii=False))

    def download_audio_of_talk(self, metadata: dict) -> None:
        self.log.debug(f"Downloading audio for {metadata.title}")
        # Download and write mp3
        download_tag = self.talk_soup.find("div", class_="row audio").find(
            "div", string="Download mp3"
        )
        download_link = download_tag.parent["href"]
        response = requests.get(download_link, stream=True)
        with open(
            f"../data/audio/{metadata.title.replace('/', ' ')}.mp3", mode="wb"
        ) as file:
            for chunk in response.iter_content(chunk_size=10 * 1024):
                file.write(chunk)


crawler = Crawler()
crawler.run()
