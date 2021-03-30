import pytest
import brownie
from brownie import Wei, accounts, Contract, config


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
    ice_rewards,
    ice,
    pid,
):
    # Shouldn't be able to call initialize again
    with brownie.reverts():
        strategy.initialize(
            vault, strategist, rewards, keeper, ice_rewards, pid, {"from": gov},
        )

    # Clone the strategy
    tx = strategy.cloneStrategy(
        vault, strategist, rewards, keeper, ice_rewards, pid, {"from": gov},
    )
    new_strategy = Strategy.at(tx.return_value)

    # Shouldn't be able to call initialize again
    with brownie.reverts():
        new_strategy.initialize(
            vault, strategist, rewards, keeper, ice_rewards, pid, {"from": gov},
        )

    # TODO: do a migrate and test a harvest
