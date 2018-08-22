import argparse
import os
import re
import sys

import requests
from requests.exceptions import HTTPError

import xml.etree.ElementTree as ET

VERBOSE = None
verbose_print = None
image_url_regex = "https://imgs.xkcd.com/comics/[A-Za-z0-9_()]+\.(png|gif|jpg)"
image_url_pattern = re.compile(image_url_regex)

comic_url_regex = "https://xkcd.com/(\d+)"
comic_url_pattern = re.compile(comic_url_regex)


def error(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


class UrlNotFoundError(Exception):
    pass


def safemkdir(directory):
    if not os.path.exists(directory):
        verbose_print("Creating directory:", directory)
        os.makedirs(directory)


def get_comic_url(id):
    url = 'https://xkcd.com/{}'.format(id)
    response = requests.get(url)
    response.raise_for_status()  # Raise any failures, if any
    html = response.text
    url = extract_img_url_from_text(html)
    if url is None:
        raise UrlNotFoundError()

    return url


def extract_img_url_from_text(data):
    match = image_url_pattern.search(data)
    if not match:
        return None
    comic_url = match.group(0)
    return comic_url


def download_comic(comic_url):
    verbose_print("Fetching comic from:", comic_url)
    comic_image = requests.get(comic_url)
    comic_image.raise_for_status()
    return comic_image


def write_contents_to_path(data, path):
    try:
        with open(path, 'wb') as file:
            file.write(data)
    except IOError:
        error("Could not save comic to file")


def download_single_comic(comic_id, output_directory, output_file_name):
    verbose_print("Downloading comic:", comic_id)
    try:
        url = get_comic_url(comic_id)
        if output_file_name is None:
            output_file_name = comic_id
        download_comic_to_file(url, output_directory, output_file_name)
    except HTTPError as e:
        error("The unable to access comic", comic_id, "because of the following reason: [", e, "]")
    except UrlNotFoundError:
        error("The specified comic could not be found")


def download_comic_to_file(url, output_directory, output_file_name):
    try:
        img_data = download_comic(url)
        extension = url.split('.')[-1]
        output_file = "{}.{}".format(output_file_name, extension)
        safemkdir(output_directory)
        verbose_print("Saving comic to", output_file)
        output_path = os.path.join(output_directory, output_file)
        write_contents_to_path(img_data.content, output_path)
    except HTTPError as e:
        error("The comic failed to download because of the following reason: [", e, "]")


def extract_comic_id(comic_url):
    match = comic_url_pattern.search(comic_url)
    return match.group(1)


def get_comic_and_url(item):
    return (extract_comic_id(item.find('link').text), extract_img_url_from_text(item.find('description').text))


def get_latest_comics_from_feed():
    rss_url = "https://xkcd.com/rss.xml"
    response = requests.get(rss_url)
    root = ET.fromstring(response.text)
    return [get_comic_and_url(item) for item in root.iter('item')]


def download_from_rss_feed(output_directory):
    try:
        for (comic_id, url) in get_latest_comics_from_feed():
            download_comic_to_file(url, output_directory, comic_id)
    except HTTPError as e:
        error("The comic failed to download because of the following reason: [", e, "]")
    except UrlNotFoundError:
        error("The specified comic could not be found")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Download yourself some XKCD comics')
    parser.add_argument('--number',
                        help='Download a specified comic by number',
                        type=int)
    parser.add_argument('--all', action='store_true',
                        help='Downloads every single XKCD comic')
    parser.add_argument('--out',
                        help='Output file name, if you are downloading a single comic')
    parser.add_argument('-v', action='store_true', help='Verbose mode')
    parser.add_argument('--dir',
                        help='The directory to which the comic should be downloaded to',
                        default='comics/')

    args = parser.parse_args()
    VERBOSE = args.v
    verbose_print = print if VERBOSE else lambda *a, **k: None
    if args.number:
        assert args.number > 0, "The comic id cannot be below 0"
        download_single_comic(args.number, args.dir, args.out)
    if not args.number and not args.all:
        download_from_rss_feed(args.dir)
    else:
        parser.print_help()
