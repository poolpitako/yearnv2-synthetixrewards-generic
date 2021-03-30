import brownie
from brownie import Contract


def test_migration(
    token,
    vault,
    chain,
    strategy,
    Strategy,
    strategist,
    whale,
    gov,
    ice_rewards,
    ice,
    pid,
):

    with brownie.reverts("Strategy already initialized"):
        strategy.initialize(vault, strategist, strategist, strategist, ice_rewards, pid)

    # Deposit to the vault and harvest
    amount = 1 * 1e18
    balance_before = token.balanceOf(whale)

    token.approve(vault, amount, {"from": whale})
    vault.deposit(amount, {"from": whale})
    strategy.harvest()

    tx = strategy.cloneStrategy(
        vault, strategist, strategist, strategist, ice_rewards, pid
    )

    # migrate to a new strategy
    new_strategy = Strategy.at(tx.return_value)

    vault.migrateStrategy(strategy, new_strategy, {"from": gov})
    assert new_strategy.estimatedTotalAssets() >= amount
    assert strategy.estimatedTotalAssets() == 0

    new_strategy.harvest({"from": gov})
    chain.sleep(3600 * 8)
    chain.mine(1)

    new_strategy.harvest({"from": gov})
    chain.sleep(3600 * 8)
    chain.mine(1)

    vault.withdraw({"from": whale})

    assert token.balanceOf(whale) > balance_before
