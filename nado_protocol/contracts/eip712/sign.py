from eth_account.signers.local import LocalAccount
from nado_protocol.contracts.eip712.domain import (
    get_eip712_domain_type,
    get_nado_eip712_domain,
)
from nado_protocol.contracts.eip712.types import (
    EIP712TypedData,
    EIP712Types,
    get_nado_eip712_type,
)
from eth_account.messages import encode_typed_data
import inspect

from nado_protocol.contracts.types import NadoTxType


def encode_eip712_typed_data(typed_data: EIP712TypedData):
    """
    eth-account's `encode_typed_data` changed its calling convention over time.
    In newer versions, passing a single positional dict is treated as `domain_data`,
    not the full message, which can raise `Invalid domain key: types`.
    """
    dumped = typed_data.model_dump()
    sig = inspect.signature(encode_typed_data)
    if "full_message" in sig.parameters:
        return encode_typed_data(full_message=dumped)
    # Older eth-account versions accepted the full EIP-712 payload as a single arg.
    return encode_typed_data(dumped)


def build_eip712_typed_data(
    tx: NadoTxType, msg: dict, verifying_contract: str, chain_id: int
) -> EIP712TypedData:
    """
    Util to build EIP712 typed data for Nado execution.

    Args:
        tx (NadoTxType): The Nado tx type being signed.

        msg (dict): The message being signed.

        verifying_contract (str): The contract that will verify the signature.

        chain_id (int): The chain ID of the originating network.

    Returns:
        EIP712TypedData: A structured data object that adheres to the EIP-712 standard.
    """
    eip17_domain = get_nado_eip712_domain(verifying_contract, chain_id)
    eip712_tx_type = get_nado_eip712_type(tx)
    eip712_primary_type = list(eip712_tx_type.keys())[0]
    eip712_types = EIP712Types(
        **{
            "EIP712Domain": get_eip712_domain_type(),
            **eip712_tx_type,
        }
    )
    return EIP712TypedData(
        domain=eip17_domain,
        primaryType=eip712_primary_type,
        types=eip712_types,
        message=msg,
    )


def get_eip712_typed_data_digest(typed_data: EIP712TypedData) -> str:
    """
    Util to get the EIP-712 typed data hash.

    Args:
        typed_data (EIP712TypedData): The EIP-712 typed data to hash.

    Returns:
        str: The hexadecimal representation of the hash.
    """
    signable_message = encode_eip712_typed_data(typed_data)
    return signable_message.hash.hex()


def sign_eip712_typed_data(typed_data: EIP712TypedData, signer: LocalAccount) -> str:
    """
    Util to sign EIP-712 typed data using a local Ethereum account.

    Args:
        typed_data (EIP712TypedData): The EIP-712 typed data to sign.

        signer (LocalAccount): The local Ethereum account to sign the data.

    Returns:
        str: The hexadecimal representation of the signature.
    """
    signable_message = encode_eip712_typed_data(typed_data)
    signed = signer.sign_message(signable_message)
    return signed.signature.hex()
