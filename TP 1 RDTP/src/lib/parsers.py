import argparse


def parse_server_config(argv=None):

    parser = argparse.ArgumentParser(
        prog="start_server", description="Start_server - The server provides file storage and download services")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true",
                       help="increase output verbosity")
    group.add_argument("-q", "--quiet", action="store_true",
                       help="decrease output verbosity")

    parser.add_argument("-H", "--host", action="store",
                        metavar="ADDR", help="service IP address")
    parser.add_argument("-p", "--port", action="store",
                        metavar="PORT", help="service port")
    parser.add_argument("-s", "--storage", action="store",
                        metavar="DIRPATH", help="storage dir path")

    args = parser.parse_args(argv)
    # Ejemplo de Args server_start
    # {'verbose': False, 'quiet': True, 'host': '192.168.0.109', 'port': '8000', 'storage': 'src/ejemplos'}
    return (args)


def parse_upload_config(argv=None):

    parser = argparse.ArgumentParser(
        prog="upload", description="Upload - upload sends a file to the server which is saved with the assigned name")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true",
                       help="increase output verbosity")
    group.add_argument("-q", "--quiet", action="store_true",
                       help="decrease output verbosity")

    parser.add_argument("-H", "--host", action="store",
                        metavar="ADDR", help="service IP address")
    parser.add_argument("-p", "--port", action="store",
                        metavar="PORT", help="service port")
    parser.add_argument("-s", "--src", action="store",
                        metavar="FILEPATH", help="source file path")
    parser.add_argument("-n", "--name", action="store",
                        metavar="FILENAME", help="file name")
    # sw: Stop and Wait
    # sr: Selective Repeate
    parser.add_argument("-r", "--protocol", action="store", metavar="protocol",
                        choices=["sw", "sr"], default="sw", help="error recovery protocol")

    args = parser.parse_args(argv)
    # Ejemplo de Args upload:
    # {'verbose': False, 'quiet': False, 'host': '127.0.0.1',
    # 'port': '8000', 'src': 'src/hola_mundo.py', 'name': 'hola_mundo.py', 'protocol': 'sw'}
    return (args)


def parse_download_config(argv=None):

    parser = argparse.ArgumentParser(
        prog="download", description="Download - download downloads a file from the server with the specified name")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true",
                       help="increase output verbosity")
    group.add_argument("-q", "--quiet", action="store_true",
                       help="decrease output verbosity")

    parser.add_argument("-H", "--host", action="store",
                        metavar="ADDR", help="service IP address")
    parser.add_argument("-p", "--port", action="store",
                        metavar="PORT", help="service port")
    parser.add_argument("-d", "--dst", action="store",
                        metavar="FILEPATH", help="destination file path")
    parser.add_argument("-n", "--name", action="store",
                        metavar="FILENAME", help="file name")
    # sw: Stop and Wait
    # sr: Selective Repeate
    parser.add_argument("-r", "--protocol", action="store", metavar="protocol",
                        choices=["sw", "sr"], default="sw", help="error recovery protocol")

    args = parser.parse_args(argv)
    # Ejemplo de Args download:
    # {'verbose': False,
    # 'quiet': False, 'host': '192.168.0.109',
    # 'port': '8000', 'dst': 'src/ejemplos', 'name': 'hola_mundo.py', 'protocol': 'sr'}
    return (args)
