"""
XKCD Parser.

A simple command line parser with a tiny bit of sophistication! Supports
download of single and multiple comics with a lil' bit of flexibility.
"""

import argparse
import os
import re

import xml.etree.ElementTree as ET

import requests
from requests.exceptions import HTTPError
from concurrent.futures import ThreadPoolExecutor
from itertools import repeat
from util import error, prefix, safemkdir, write_contents_to_path, yes_no_prompt


VERBOSE = None
verbose_print = None
image_url_regex = "https://imgs.xkcd.com/comics/[A-Za-z0-9_()]+\.(png|gif|jpg)"
image_url_pattern = re.compile(image_url_regex)

comic_url_regex = "https://xkcd.com/(\d+)"
comic_url_pattern = re.compile(comic_url_regex)


class UrlNotFoundError(Exception):
    """Exception raised when the image URL couldn't be extracted."""


def get_comic_image_url(id):
    """Retrieve the image URL from a comic."""
    url = 'https://xkcd.com/{}'.format(id)
    response = requests.get(url)
    response.raise_for_status()  # Raise any failures, if any
    html = response.text
    url = extract_img_url_from_text(html)
    if url is None:
        raise UrlNotFoundError()

    return url


def extract_img_url_from_text(data):
    """Extract the image URL pattern from any text."""
    match = image_url_pattern.search(data)
    if not match:
        return None
    comic_url = match.group(0)
    return comic_url


def download_comic(comic_url):
    """Download the comic image data."""
    verbose_print("Fetching comic from:", comic_url)
    comic_image = requests.get(comic_url)
    comic_image.raise_for_status()
    return comic_image


def download_single_comic(comic_id, output_directory, output_file_name):
    """Download a single comic by ID and write to a file."""
    print("Downloading comic:", comic_id)
    try:
        url = get_comic_image_url(comic_id)
        if output_file_name is None:
            output_file_name = comic_id
        download_comic_to_file(url, output_directory, output_file_name)
    except HTTPError as e:
        error("The unable to access comic", comic_id, "because of the following reason: [", e, "]")
    except UrlNotFoundError:
        error("The specified comic could not be found")


def download_comic_to_file(url, output_directory, output_file_name):
    """Download a comic from the URL and write to a file."""
    try:
        img_data = download_comic(url)
        extension = url.split('.')[-1]
        output_file = "{}.{}".format(output_file_name, extension)
        verbose_print("Creating directory:", output_directory)
        safemkdir(output_directory)
        verbose_print("Saving comic to", output_file)
        output_path = os.path.join(output_directory, output_file)
        write_contents_to_path(img_data.content, output_path)
    except HTTPError as e:
        error("The comic failed to download because of the following reason: [", e, "]")
    except IOError:
        error("Could not save comic to file")


def extract_comic_id(comic_url):
    """Search for the comic ID given the comic URL."""
    match = comic_url_pattern.search(comic_url)
    return match.group(1)


def get_comic_and_url(item):
    """Extract the comic ID and URL from the RSS feed item tag."""
    return (extract_comic_id(item.find('link').text), extract_img_url_from_text(item.find('description').text))


def get_latest_comics_from_feed():
    """Get the list of comic and URLs from the RSS feed."""
    rss_url = "https://xkcd.com/rss.xml"
    response = requests.get(rss_url)
    root = ET.fromstring(response.text)
    return [get_comic_and_url(item) for item in root.iter('item')]


def download_from_rss_feed(output_directory, file_prefix):
    """Download comics from the RSS feed."""
    try:
        if file_prefix is None:
            file_prefix = ""
        for (comic_id, url) in get_latest_comics_from_feed():
            download_comic_to_file(url, output_directory, file_prefix + comic_id)
    except HTTPError as e:
        error("The comic failed to download because of the following reason: [", e, "]")
    except UrlNotFoundError:
        error("The specified comic could not be found")


def build_argparser():
    """Build an arg parser for the script."""
    parser = argparse.ArgumentParser(
        description='Download yourself some XKCD comics')
    parser.add_argument('--number',
                        help='Download a specified comic by number',
                        type=int)
    parser.add_argument('--all', action='store_true',
                        help='Downloads every single XKCD comic')
    parser.add_argument('--out',
                        help='Output file name, if you are downloading a single comic or a prefix if downloading several')
    parser.add_argument('-v', action='store_true', help='Verbose mode')
    parser.add_argument('--dir',
                        help='The directory to which the comic should be downloaded to',
                        default='comics/')
    return parser


def download_all_comics(output_directory, file_prefix):
    """Download every comic getting the latest comic id from the RSS feed."""
    max_comic_id = 1
    for (comic_id, _) in get_latest_comics_from_feed():
        comic_id = int(comic_id)
        if max_comic_id < comic_id:
            max_comic_id = comic_id

    comic_id_list = list(range(1, max_comic_id + 1))
    if file_prefix:
        file_name_list = prefix(file_prefix, comic_id_list)
    else:
        file_name_list = comic_id_list
    # Kept a default of 10. We don't want to leech off XKCD.com
    executor = ThreadPoolExecutor(max_workers=10)
    executor.map(download_single_comic, comic_id_list, repeat(output_directory), file_name_list)


if __name__ == "__main__":
    parser = build_argparser()
    args = parser.parse_args()
    VERBOSE = args.v
    verbose_print = print if VERBOSE else lambda *a, **k: None
    if args.number:
        if args.number > 0:
            download_single_comic(args.number, args.dir, args.out)
        else:
            error("The comic number must be at least 1")
    elif args.all:
        download_all_comics(args.dir, args.out)
    else:
        if yes_no_prompt("Do you want to download the latest handful of comics from the RSS feed?"):
            download_from_rss_feed(args.dir, args.out)
        else:
            parser.print_help()
