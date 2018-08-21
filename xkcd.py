import argparse
import requests
import re
import os
import sys
from requests.exceptions import HTTPError

VERBOSE = None
verbose_print = None
image_url_pattern = re.compile("https://imgs.xkcd.com/comics/[A-Za-z0-9_()]+\.(png|gif|jpg)")


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
    response.raise_for_status() # Raise any failures, if any
    html = response.text
    match = image_url_pattern.search(html)
    if not match:
        raise UrlNotFoundError()
    comic_url = match.group(0)
    return comic_url


def download_comic(comic_url):
    verbose_print("Fetching comic from:", comic_url)
    comic_image = requests.get(comic_url)
    return comic_image


def write_contents_to_path(data, path):
    try:
        with open(path, 'wb') as file:
            file.write(data)
    except IOError as e:
        error("Could not save comic to file")

def download_single_comic(comic_id, output_directory, output_file_name):
    verbose_print("Downloading comic:", comic_id)
    try:
        url = get_comic_url(comic_id)
        img_data = download_comic(url)
        extension = url.split('.')[-1]
        if not output_file_name:
            output_file_name = comic_id
        output_file = "{}.{}".format(output_file_name, extension)
        safemkdir(output_directory)
        output_path = os.path.join(output_directory, output_file)
        verbose_print("Saving comic to", output_path)
        write_contents_to_path(img_data.content, output_path)
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
        download_single_comic(args.number, args.dir, args.out)
    else:
        parser.print_help()