import brownie
from brownie import Contract, Wei


def test_human_vs_auto(
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

    # Update first strategy and create a second one
    vault.updateStrategyDebtRatio(strategy, 5_000, {"from": gov})
    tx = strategy.cloneStrategy(
        vault, strategist, strategist, strategist, ice_rewards, pid
    )
    manual_harvest_strategy = Strategy.at(tx.return_value, owner=gov)
    vault.addStrategy(
        manual_harvest_strategy, 5_000, 0, 2 ** 256 - 1, 1_000, {"from": gov}
    )
    assert vault.debtRatio() == 10_000

    # Deposit to the vault and harvest
    amount = Wei("100 ether")
    token.approve(vault, amount, {"from": whale})
    vault.deposit(amount, {"from": whale})

    # Do the investment
    strategy.harvest()
    manual_harvest_strategy.harvest()
    chain.sleep(3600 * 8)
    chain.mine(1)

    assert strategy.balanceOfStake() == manual_harvest_strategy.balanceOfStake()

    # Harvest strategy several times
    for i in range(0, 50):
        strategy.harvest()
        chain.sleep(60 * 60 * 8)
        chain.mine(1)

    # Harvest both one last time
    strategy.harvest()
    manual_harvest_strategy.harvest()
    chain.sleep(3600 * 8)
    chain.mine(1)

    automatic_gain = vault.strategies(strategy).dict()["totalGain"]
    manual_gain = vault.strategies(manual_harvest_strategy).dict()["totalGain"]
    print(f"Automatic gained {(automatic_gain-manual_gain)/1e18} more than manual")
