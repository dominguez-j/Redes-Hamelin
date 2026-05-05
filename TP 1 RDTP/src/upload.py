from lib.client.client import Client
from lib.common.constants import UPLOAD
from lib.parsers import parse_upload_config


def main():

    args = parse_upload_config()
    Client((args.host, int(args.port)), (args.verbose, args.quiet),
           args.src, args.name, UPLOAD, args.protocol)


if __name__ == "__main__":
    main()
