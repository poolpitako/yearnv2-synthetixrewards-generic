import pytest
import brownie
from brownie import Wei, accounts, Contract, config


@pytest.mark.require_network("mainnet-fork")
def test_clone(
    chain,
    gov,
    strategist,
    rewards,
    keeper,
    strategy,
    Strategy,
    vault,
    token,
    yfibank,
    bank,
    router,
):
    # Shouldn't be able to call initialize again
    with brownie.reverts():
        strategy.initialize(
            vault,
            strategist,
            rewards,
            keeper,
            yfibank,
            router,
            token,
            bank,
            {"from": gov},
        )

    # Clone the strategy
    tx = strategy.cloneStrategy(
        vault,
        strategist,
        rewards,
        keeper,
        yfibank,
        router,
        token,
        bank,
        {"from": gov},
    )
    new_strategy = Strategy.at(tx.return_value)

    # Shouldn't be able to call initialize again
    with brownie.reverts():
        new_strategy.initialize(
            vault,
            strategist,
            rewards,
            keeper,
            yfibank,
            router,
            token,
            bank,
            {"from": gov},
        )


    # TODO: do a migrate and test a harvest
