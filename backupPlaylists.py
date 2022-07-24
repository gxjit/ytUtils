from argparse import ArgumentParser, ArgumentTypeError
from json import dumps
from pathlib import Path
from pprint import pprint
from re import sub as subStr
from unicodedata import normalize

from ytmusicapi import YTMusic

print = pprint
yt = YTMusic()


efilter = lambda func, itr: tuple(filter(func, itr))

emap = lambda func, itr: tuple(map(func, itr))


def csvToList(vals):
    if "," in vals:
        return efilter(len, vals.strip().split(","))
    else:
        return [vals]


def checkDirPath(pth):
    pthObj = Path(pth)
    if pthObj.is_dir():
        return pthObj
    else:
        raise ArgumentTypeError("Invalid Directory path")


def cliArgs():
    parser = ArgumentParser(description="Backup Youtube/Youtube Music playlists to json.")
    parser.add_argument(
        "id", help="Comma separated id(s) of playlist(s).", type=csvToList
    )
    parser.add_argument(
        "-r",
        "--raw",
        action="store_true",
        help="Dump raw playlist data from ytmusicapi.",
    )
    parser.add_argument(
        "-d",
        "--dir",
        default=Path.cwd(),
        type=checkDirPath,
        help="Output directory.",
    )
    return parser.parse_args()


def slugify(
    value,
    allowUnicode=False,
    replace=True,
    keepSpace=True,
    keepDots=True,
    lowerCase=False,
    swap={},
):
    """
    Adapted from django.utils.text.slugify
    """
    value = str(value)
    if allowUnicode:
        value = normalize("NFKC", value)
    else:
        value = normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    swap = {"[": "(", "]": ")", **swap}
    for k, v in swap.items():
        value = value.replace(k, v)
    rejectPattern = r"[^\w\s)(_-]+"  # r"[^\w\s)(_-]"
    if keepDots:
        rejectPattern = rejectPattern.replace(r"\s", r"\s.")
    replaceWith = "_" if replace else ""
    value = subStr(rejectPattern, replaceWith, value).strip()
    if lowerCase:
        value = value.lower()
    if not keepSpace:
        value = subStr(r"[-\s]+", "-", value)
    return value


def filterPlaylistData(data):
    d = data
    playlistInfo = {
        "id": d["id"],
        "title": d["title"],
        "author": d["author"]["name"],
        "privacy": d["privacy"],
        "tracks": d["trackCount"],
        "length": d["duration_seconds"],
    }
    del d
    # print(data["title"])

    tracks = [
        {
            "id": t["videoId"],
            "title": t["title"],
            "artists": ", ".join([a["name"] for a in t["artists"]]),
            "album": t["album"] and t["album"].get("name"),
            "length": t["duration_seconds"],
        }
        for t in data["tracks"]
    ]

    return {**playlistInfo, "tracks": [{**t} for t in tracks]}


def dumpPlaylist(jsonData, ext=".json"):
    Path(Path.cwd() / f"{slugify(jsonData['title'])}{ext}").write_text(
        dumps(jsonData, indent=2)
    )

def main():
    pargs = cliArgs()
    rawData = emap(yt.get_playlist, pargs.id)
    if pargs.raw:
        ext = ".raw.json"
        dumpPlaylistP = lambda d: dumpPlaylist(d, ext)
        emap(dumpPlaylistP, rawData)
    else:
        for d in rawData:
            dumpPlaylist(filterPlaylistData(d))


if __name__ == "__main__":
    main()
