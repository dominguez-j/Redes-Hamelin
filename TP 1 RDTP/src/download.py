from lib.client.client import Client
from lib.common.constants import DOWNLOAD
from lib.parsers import parse_download_config


def main():

    args = parse_download_config()
    Client((args.host, int(args.port)), (args.verbose, args.quiet),
           args.dst, args.name, DOWNLOAD, args.protocol)


if __name__ == "__main__":
    main()
