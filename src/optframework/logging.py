"""
Logging do framework, via loguru.

Como o framework é reaplicável em outros projetos (ver README), o `logger` fica
**desabilitado por padrão** — é o comportamento recomendado pela própria documentação do
loguru para bibliotecas
(https://loguru.readthedocs.io/en/stable/resources/recipes.html#using-loguru-in-a-library):
uma lib não deve decidir sinks/formato pela aplicação que a consome. Um projeto que usa o
framework escolhe entre duas formas de ligar os logs:

- `configure_logging()`: setup pronto, sink colorido no stderr, sem lidar com a API do loguru.
- Ou, se o projeto já usa loguru para si: `from loguru import logger;
  logger.enable("optframework")` e registrar os próprios sinks.
"""

from __future__ import annotations

import sys
from typing import Any

from loguru import logger

__all__ = ["configure_logging", "logger"]

logger.disable("optframework")

_DEFAULT_FORMAT = (
    "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
)


def configure_logging(
    level: str = "INFO",
    *,
    sink: Any = sys.stderr,
    colorize: bool = True,
    fmt: str = _DEFAULT_FORMAT,
    **sink_kwargs: Any,
) -> int:
    """
    Habilita o logger do framework e registra um sink colorido (default: stderr).

    Conveniência para quem só quer "ver os logs do framework" sem lidar com a API do
    loguru diretamente. Devolve o id do handler, para desfazer com `logger.remove(id)`.
    """
    logger.enable("optframework")
    return logger.add(sink, level=level, colorize=colorize, format=fmt, **sink_kwargs)
