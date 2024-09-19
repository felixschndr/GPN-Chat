import json
from html import unescape

import requests
from bs4 import BeautifulSoup

from source.logger import LoggerMixin

TO_REPLACE_CHARACTERS = {
    "/": " ",
    "?": "",
    "<": "",
    ">": "",
    ":": "",
    '"': "",
    "|": "",
    "*": "",
}


class Crawler(LoggerMixin):
    def __init__(self):
        super().__init__()
        self.BASE_URL = "https://media.ccc.de"
        self.CONFERENCES_URL = f"{self.BASE_URL}/b/conferences/gpn"
        self.conferences_links = []
        self.gpns = []
        self.talks = {}

    def run(self) -> None:
        """
        This method is used to run the software. It performs the following steps:
        1. Retrieves the conference links and gpns using the method `get_conferences_and_gpns()`.
        2. Retrieves the talks using the method `get_talks()`.
        3. Logs the absolute number of talks using the `log.debug()` method.
        4. Creates and writes the metadata of the talks using the method `create_and_write_metadata_of_talks()`.
        5. Logs the message "Metadata files created" using the `log.debug()` method.
        6. Downloads the audio files of the talks using the method `download_audio_of_talks()`.
        7. Logs the message "Audio files downloaded" using the `log.debug()` method.

        :return: None
        """
        self.conferences_links, self.gpns = self.get_conferences_and_gpns()
        self.talks = self.get_talks()
        self.log.debug(f"Absolute number of talks: {len(self.talks)}")
        self.create_and_write_metadata_of_talks()
        self.log.debug("Metadata files created")
        self.download_audio_of_talks()
        self.log.debug("Audio files downloaded")

    def get_conferences_and_gpns(self) -> tuple[list, list]:
        """
        Retrieves the conferences and GPNs from the given URL.

        :return: A tuple containing two lists.
        The first list contains the URLs of the conferences, and the second list contains the corresponding gpns.
        """
        conferences_page = requests.get(self.CONFERENCES_URL).content

        conferences_soup = BeautifulSoup(conferences_page, "html.parser")
        conferences = conferences_soup.find_all("a", class_="thumbnail conference")
        conferences_links = []
        gpns = []
        for conference in conferences:
            link = conference["href"]
            conferences_links.append(link)
            gpn = link.split("/")[-1]
            gpns.append(gpn)

        return conferences_links, gpns

    def get_talks(self) -> dict[str, dict]:
        """
        This method is used to fetch information about talks from conference websites. It scrapes the conference websites and retrieves the titles and links of the talks.

        :return: A dictionary containing talk information. The keys of the dictionary are the titles of the talks, and the values are dictionaries with the following keys:
            - "title": The title of the talk.
            - "link": The link to the talk.
            - "gpn": The GPN (Global Presentation Number) associated with the talk.
        """
        talks = {}
        for index, conference_link in enumerate(self.conferences_links):
            conference_site = requests.get(self.BASE_URL + conference_link).content
            conference_soup = BeautifulSoup(conference_site, "html.parser")
            talk_elements = conference_soup.find_all("h3")
            for talk_element in talk_elements:
                link_element = talk_element.find("a")
                title = link_element.text.replace("\n", "")
                for char in TO_REPLACE_CHARACTERS.keys():
                    title = title.replace(char, TO_REPLACE_CHARACTERS[char])
                link = link_element["href"]
                talks[title] = {"title": title, "link": link, "gpn": self.gpns[index]}

        return talks

    def create_and_write_metadata_of_talks(self) -> None:
        """
        This method is used to create and write metadata of talks.
        It retrieves data from a website and populates the metadata for each talk.

        :return: None
        """
        for index, talk in enumerate(self.talks.values(), start=1):
            self.log.debug(f"Creating metadata file for #{index} talk: {talk['title']}")

            talk_site = requests.get(self.BASE_URL + talk["link"]).content
            talk_soup = BeautifulSoup(talk_site, "html.parser")
            speaker_paragraphs = talk_soup.find("p", class_="persons").find_all("a")
            speakers = []
            for speaker in speaker_paragraphs:
                speakers.append(speaker.text.replace("\n", ""))

            metadata_list = talk_soup.find("ul", class_="metadata")
            metadata = metadata_list.find_all("li")
            duration = metadata[0].text.replace("\n", "")
            date = metadata[1].text.replace("\n", "")

            description_paragraph = talk_soup.find("p", class_="description")
            description = (
                description_paragraph.text.replace("\n", "")
                if description_paragraph
                else ""
            )
            description = unescape(description)

            metadata = {
                "speakers": speakers,
                "duration": duration,
                "date": date,
                "description": description,
            }

            talk |= metadata

            self.write_metadata_of_talk(talk)

    @staticmethod
    def write_metadata_of_talk(talk: dict) -> None:
        """
        Writes metadata of talk to a file.

        :param talk: The metadata of the talk as a dictionary.
        :return: None
        """
        with open(
            f"../data/metadata/{talk['title']}.json",
            mode="w",
            encoding="utf-8",
        ) as file:
            file.write(json.dumps(talk, indent=4, ensure_ascii=False))

    def download_audio_of_talks(self) -> None:
        """
        Downloads the audio for each talk in the `self.talks` dictionary.
        It retrieves the talk's page from the provided `BASE_URL` and parses it using BeautifulSoup.
        It then searches for the audio file download link and downloads the mp3 file.

        :return: None
        """
        for index, (talk_title, talk) in enumerate(self.talks.items(), start=1):
            self.log.debug(f"Downloading audio for #{index} talk: {talk_title}")
            talk_site = requests.get(self.BASE_URL + talk["link"]).content
            talk_soup = BeautifulSoup(talk_site, "html.parser")
            audio_row = talk_soup.find("div", class_="row audio")
            if not audio_row:
                self.log.debug(
                    f"No audio found for talk: {talk_title}, continuing with next talk..."
                )
                continue

            download_tag = audio_row.find("div", string="Download mp3")
            download_link = download_tag.parent["href"]
            response = requests.get(download_link, stream=True)
            with open(f"../data/audio/{talk_title}.mp3", mode="wb") as file:
                for chunk in response.iter_content(chunk_size=10 * 1024):
                    file.write(chunk)
