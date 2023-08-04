from prometheus_client import start_http_server
from web3.middleware import simple_cache_middleware

from src import variables
from src.handlers.exit import ExitsHandler
from src.handlers.fork import ForkHandler
from src.handlers.slashing import SlashingHandler
from src.metrics.healthcheck_server import start_pulse_server
from src.metrics.logging import logging
from src.watcher import Watcher
from src.web3py.extensions import FallbackProviderModule, LidoContracts
from src.web3py.middleware import metrics_collector
from src.web3py.typings import Web3

logger = logging.getLogger()


def main():
    logger.info({'msg': 'Ethereum head watcher startup.'})

    logger.info({'msg': f'Start healthcheck server for Docker container on port {variables.HEALTHCHECK_SERVER_PORT}'})
    start_pulse_server()

    logger.info({'msg': f'Start http server with prometheus metrics on port {variables.PROMETHEUS_PORT}'})
    start_http_server(variables.PROMETHEUS_PORT)

    web3 = Web3(
        FallbackProviderModule(variables.EXECUTION_CLIENT_URI, request_kwargs={'timeout': variables.EL_REQUEST_TIMEOUT})
    )
    web3.attach_modules(
        {
            'lido_contracts': LidoContracts,
        }
    )
    web3.middleware_onion.add(metrics_collector)
    web3.middleware_onion.add(simple_cache_middleware)

    if variables.DRY_RUN:
        logger.warning({'msg': 'Dry run mode enabled! No alerts will be sent.'})

    handlers = [
        SlashingHandler(),
        ForkHandler(),
        ExitsHandler(),
        # FinalityHandler(), ???
    ]
    Watcher(handlers, web3).run()


if __name__ == "__main__":
    errors = variables.check_uri_required_variables()
    variables.raise_from_errors(errors)
    main()
