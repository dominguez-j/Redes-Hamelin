import unittest

from lib.parsers import (
    parse_server_config,
    parse_upload_config,
    parse_download_config
)


class TestParser(unittest.TestCase):

    def test_rejects_invalid_protocol(self):

        with self.assertRaises(SystemExit):
            parse_upload_config([
                "-H", "127.0.0.1",
                "-p", "8000",
                "-s", "src/hola_mundo.py",
                "-n", "hola_mundo.py",
                "-r", "tcp",
            ])

    def test_rejects_verbose_and_quiet_together(self):

        with self.assertRaises(SystemExit):
            parse_upload_config([
                "-v", "-q", "-H", "127.0.0.1"
            ])

    def test_valid_start_server(self):

        args = parse_server_config([
            "-q",
            "-H", "192.168.0.1",
            "-p", "9000",
            "-s", "files",
        ])

        self.assertFalse(args.verbose)
        self.assertTrue(args.quiet)
        self.assertEqual(args.host, "192.168.0.1")
        self.assertEqual(args.port, "9000")
        self.assertEqual(args.storage, "files")

    def test_valid_upload(self):
        args = parse_upload_config([
            "-H", "127.0.0.1",
            "-p", "9000",
            "-s", "src/hola_mundo.py",
            "-n", "hola_mundo.py",
        ])

        self.assertFalse(args.verbose)
        self.assertFalse(args.quiet)
        self.assertEqual(args.host, "127.0.0.1")
        self.assertEqual(args.port, "9000")
        self.assertEqual(args.src, "src/hola_mundo.py")
        self.assertEqual(args.name, "hola_mundo.py")
        self.assertEqual(args.protocol, "sw")

    def test_valid_download_config(self):

        args = parse_download_config([
            "-v",
            "-H", "192.168.0.1",
            "-p", "9000",
            "-d", "src/lib/",
            "-n", "parsers.py",
        ])

        self.assertTrue(args.verbose)
        self.assertFalse(args.quiet)
        self.assertEqual(args.host, "192.168.0.1")
        self.assertEqual(args.port, "9000")
        self.assertEqual(args.dst, "src/lib/")
        self.assertEqual(args.name, "parsers.py")
        self.assertEqual(args.protocol, "sw")


def main():
    unittest.main()


if __name__ == "__main__":
    main()
