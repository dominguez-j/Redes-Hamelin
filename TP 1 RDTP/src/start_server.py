from lib.parsers import parse_server_config
from lib.server.server import Server


def main():

    args = parse_server_config()
    Server((args.host, int(args.port)),
           (args.verbose, args.quiet), args.storage)


if __name__ == "__main__":
    main()
