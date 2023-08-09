import json
import logging
from time import sleep

from web3 import Web3
from web3.contract import Contract
from web3.exceptions import BadFunctionCallOutput
from web3.module import Module

from src import variables

logger = logging.getLogger()


class LidoContracts(Module):
    lido_locator: Contract
    lido: Contract
    accounting_oracle: Contract
    staking_router: Contract
    validators_exit_bus_oracle: Contract
    withdrawal_queue_nft: Contract
    oracle_report_sanity_checker: Contract
    oracle_daemon_config: Contract
    burner: Contract

    def __init__(self, w3: Web3):
        super().__init__(w3)
        self._load_contracts()

    def __setattr__(self, key, value):
        current_value = getattr(self, key, None)
        if isinstance(current_value, Contract) and isinstance(value, Contract):
            if value.address != current_value.address:
                logger.info({'msg': f'Contract {key} has been changed to {value.address}'})
        super().__setattr__(key, value)

    def has_contract_address_changed(self) -> bool:
        addresses = [contract.address for contract in self.__dict__.values() if isinstance(contract, Contract)]
        self._load_contracts()
        new_addresses = [contract.address for contract in self.__dict__.values() if isinstance(contract, Contract)]
        return addresses != new_addresses

    def _check_contracts(self):
        """This is startup check that checks that contract are deployed and has valid implementation"""
        try:
            self.accounting_oracle.functions.getContractVersion().call()
            self.validators_exit_bus_oracle.functions.getContractVersion().call()
        except BadFunctionCallOutput:
            logger.info(
                {
                    'msg': 'getContractVersion method from accounting_oracle and validators_exit_bus_oracle '
                    'doesn\'t return any data. Probably addresses from Lido Locator refer to the wrong '
                    'implementation or contracts don\'t exist. Sleep for 1 minute.'
                }
            )
            sleep(60)
            self._load_contracts()
        else:
            return

    def _load_contracts(self):
        # Contract that stores all lido contract addresses
        self.lido_locator = self.w3.eth.contract(
            address=variables.LIDO_LOCATOR_ADDRESS,
            abi=self.load_abi('LidoLocator'),
            decode_tuples=True,
        )

        self.lido = self.w3.eth.contract(
            address=self.lido_locator.functions.lido().call(),
            abi=self.load_abi('Lido'),
            decode_tuples=True,
        )

        self.accounting_oracle = self.w3.eth.contract(
            address=self.lido_locator.functions.accountingOracle().call(),
            abi=self.load_abi('AccountingOracle'),
            decode_tuples=True,
        )

        self.staking_router = self.w3.eth.contract(
            address=self.lido_locator.functions.stakingRouter().call(),
            abi=self.load_abi('StakingRouter'),
            decode_tuples=True,
        )

        self.validators_exit_bus_oracle = self.w3.eth.contract(
            address=self.lido_locator.functions.validatorsExitBusOracle().call(),
            abi=self.load_abi('ValidatorsExitBusOracle'),
            decode_tuples=True,
        )

        self.withdrawal_queue_nft = self.w3.eth.contract(
            address=self.lido_locator.functions.withdrawalQueue().call(),
            abi=self.load_abi('WithdrawalQueueERC721'),
            decode_tuples=True,
        )

        self.oracle_report_sanity_checker = self.w3.eth.contract(
            address=self.lido_locator.functions.oracleReportSanityChecker().call(),
            abi=self.load_abi('OracleReportSanityChecker'),
            decode_tuples=True,
        )

        self.oracle_daemon_config = self.w3.eth.contract(
            address=self.lido_locator.functions.oracleDaemonConfig().call(),
            abi=self.load_abi('OracleDaemonConfig'),
            decode_tuples=True,
        )

        self.burner = self.w3.eth.contract(
            address=self.lido_locator.functions.burner().call(),
            abi=self.load_abi('Burner'),
            decode_tuples=True,
        )

        self._check_contracts()

    @staticmethod
    def load_abi(abi_name: str, abi_path: str = './assets/'):
        with open(f'{abi_path}{abi_name}.json') as f:
            return json.load(f)
