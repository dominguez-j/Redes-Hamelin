import io
import unittest
import logging
from lib.logger import Logger

_FORMAT_TESTING = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


class TestLogger(unittest.TestCase):

    def _setup_log_for_testing(self, my_log_name: str, verbose: bool, quiet: bool):
        # Creación del Handler para logging de mensajes de DEBUG
        # los mensajes se guardan en un buffer para el testeo
        buffer = io.StringIO()
        my_log = Logger(my_log_name, verbose, quiet)
        buffer_handler = logging.StreamHandler(buffer)
        buffer_handler.setLevel(logging.DEBUG)
        buffer_handler.setFormatter(
            logging.Formatter(_FORMAT_TESTING, datefmt="%H:%M:%S")
        )
        my_log.logger.addHandler(buffer_handler)
        return my_log, buffer

    def tearDown(self):
        for attr in vars(self).values():
            if isinstance(attr, Logger):
                attr.close()

    # Cuando es Verbose, se imprimen todos los tipos incluso level DEBUG
    def test_verbose_debug(self):
        # Testo que el mensaje DEBUG aparece en el Buffer
        my_log, buffer = self._setup_log_for_testing("test_verbose_message_debug", verbose=True, quiet=False)
        my_log.debug("mensaje de debug")

        output = buffer.getvalue()
        self.assertIn("mensaje de debug", output)

    def test_verbose_error(self):
        # En verbose, ERROR también debe aparecer
        my_log, buffer = self._setup_log_for_testing("test_verbose_message_error", verbose=True, quiet=False)
        my_log.error("mensaje de error")

        output = buffer.getvalue()
        self.assertIn("mensaje de error", output)

    # Cuando es Verbose, se imprimen los mensajes del level hasta INFO
    def test_verbose_info(self):
        # En verbose, INFO también debe aparecer
        my_log, buffer = self._setup_log_for_testing("test_verbose_message_info_and_warning", verbose=True, quiet=False)
        my_log.info("mensaje de info")
        my_log.warning("mensaje de warning")

        output = buffer.getvalue()
        self.assertIn("mensaje de info", output)
        self.assertIn("mensaje de warning", output)

    def test_quiet_info(self):
        # En Quiet, se imprimen los mensajes del level ERROR
        my_log, buffer = self._setup_log_for_testing("test_quiet_message_error", verbose=False, quiet=True)
        my_log.error("mensaje de info en quiet")
        # Este mensaje de ERROR no tiene que aparecer
        my_log.debug("mensaje de debug en quiet")

        output = buffer.getvalue()
        self.assertIn("mensaje de info en quiet", output)
        self.assertNotIn("mensaje de debug en quiet", output)

    # Cuando no es ni Verbose ni Quiet, se imprimen los mensajes level INFO
    def test_debug_message_for_default(self):

        my_log, buffer = self._setup_log_for_testing("test_default_message_info", verbose=False, quiet=False)
        my_log.info("mensaje de info en default")
        # Este mensaje DEBUG no debería aparecer en buffer porque no estamos en Verbose
        my_log.debug("mensaje de debug en default")
        # Este mensaje ERROR deberia aaprecer porque ERROR tiene un level inferior a INFO
        my_log.error("mensaje de error en default")

        output = buffer.getvalue()
        self.assertIn("mensaje de info en default", output)
        self.assertIn("mensaje de error en default", output)
        self.assertNotIn("mensaje de debug en default", output)


if __name__ == '__main__':
    unittest.main()
