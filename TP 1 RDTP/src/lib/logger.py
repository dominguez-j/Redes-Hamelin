import sys
import logging

# Formato: Tiempo - [Level] - nombre del logger: Mensaje
_FORMAT_VERBOSE = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_FORMAT_NORMAL = '%(message)s'

# Levels:
#    Verbolsidad - Más Alta: DEBUG:   Información detallada y valores de variables. Se imprimen:
#                                     DEBUG + INFO + WARNING + ERROR
#    Verbosidad - Alta:      INFO:    Mensajes confirmando que las cosas funcionan como se espera.
#                                     Se imprimen:
#                                     INFO + WARNING + ERROR
#    Verbosidad - Media:     WARNING: Una señal de alerta de que algo raro pasó o podría pasar,
#                                     pero no es un error todavía (Default Python). Se imprimen:
#                                     WARNING + ERROR
#    Verbosidad - Baja:      ERROR:   Problemas serios, pero el programa puede seguir intentando
#                                     otras tareas


class Logger:
    def __init__(self, logger_name: str, verbose: bool, quiet: bool):
        self.logger = logging.getLogger(logger_name)
        if not self.logger.handlers:
            self._init_setting(verbose, quiet)

    def _init_setting(self, verbose: bool, quiet: bool) -> None:
        if verbose:
            self.logger.setLevel(logging.DEBUG)
        elif quiet:
            self.logger.setLevel(logging.ERROR)
        else:
            self.logger.setLevel(logging.INFO)

        if verbose:
            format_str = _FORMAT_VERBOSE
        else:
            format_str = _FORMAT_NORMAL

        formatter = logging.Formatter(format_str, datefmt="%H:%M:%S")

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        self.logger.propagate = False

    def debug(self, msg: str, *args, **kwargs) -> None:
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        self.logger.error(msg, *args, **kwargs)

    def close(self):
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)
