import argparse
import requests
import re
import os
import sys

VERBOSE = None
verbose_print = None
image_url_pattern = re.compile("https://imgs.xkcd.com/comics/[A-Za-z0-9_()]+\.(png|gif|jpg)")


def error(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


class UrlNotFoundError(Exception):
    pass


def get_comic_url(id):
    url = 'https://xkcd.com/{}'.format(id)
    response = requests.get(url)
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


def download_single_comic(comic_id, output_directory, output_file):
    verbose_print("Downloading comic:", comic_id)
    try:
        url = get_comic_url(comic_id)
        image = download_comic(url)
        if not output_file:
            extension = url.split('.')[-1]
            output_file_name = "{}.{}".format(comic_id, extension)
            output_file = open(output_file_name, 'wb')
        verbose_print("Saving comic to", output_file.name)
        output_file.write(image.content)
        output_file.close()
    except UrlNotFoundError:
        error("The specified comic could not be found")
        if output_file:
            output_file.close()
            os.remove(output_file.name)
    except IOError as e:
        error("Could not save comic to file")
        if output_file:
            output_file.close()
            os.remove(output_file.name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Download yourself some XKCD comics')
    parser.add_argument('--number',
                        help='Download a specified comic by number',
                        type=int)
    parser.add_argument('--all', action='store_true',
                        help='Downloads every single XKCD comic')
    parser.add_argument('--range',
                        help='Downloads comics from the specified range')
    parser.add_argument('--out',
                        help='Output file name, if you are downloading a single comic',
                        type=argparse.FileType('wb'))
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