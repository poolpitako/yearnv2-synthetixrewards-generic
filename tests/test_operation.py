import brownie
from brownie import Contract, Wei
from useful_methods import genericStateOfVault, genericStateOfStrat
import random


def test_apr(accounts, token, vault, strategy, chain, strategist, whale):
    strategist = accounts[0]

    amount = 1 * 1e18
    # Deposit to the vault
    token.approve(vault, amount, {"from": whale})
    vault.deposit(amount, {"from": whale})
    assert token.balanceOf(vault) == amount

    # harvest
    strategy.harvest()
    startingBalance = vault.totalAssets()
    for i in range(2):

        waitBlock = 50
        print(f"\n----wait {waitBlock} blocks----")
        chain.mine(waitBlock)
        chain.sleep(waitBlock * 13)
        print(f"\n----harvest----")
        strategy.harvest({"from": strategist})

        genericStateOfStrat(strategy, token, vault)
        genericStateOfVault(vault, token)

        profit = (vault.totalAssets() - startingBalance) / 1e18
        strState = vault.strategies(strategy)
        totalReturns = strState[7]
        totaleth = totalReturns / 1e18
        print(f"Real Profit: {profit:.5f}")
        difff = profit - totaleth
        print(f"Diff: {difff}")

        blocks_per_year = 2_252_857
        assert startingBalance != 0
        time = (i + 1) * waitBlock
        assert time != 0
        apr = (totalReturns / startingBalance) * (blocks_per_year / time)
        assert apr > 0
        print(apr)
        print(f"implied apr: {apr:.8%}")


def test_normal_activity(accounts, token, vault, strategy, strategist, whale, chain):

    amount = Wei("1 ether")
    balance_before = token.balanceOf(whale)

    # Deposit to the vault
    token.approve(vault, amount, {"from": whale})
    vault.deposit(amount, {"from": whale})
    assert token.balanceOf(vault) == amount

    # invest
    strategy.harvest()
    chain.sleep(8 * 3600)
    chain.mine(1)

    # harvest some profits
    strategy.harvest()
    chain.sleep(8 * 3600)
    chain.mine(1)

    # withdrawal
    vault.withdraw({"from": whale})

    assert token.balanceOf(whale) > balance_before

    genericStateOfStrat(strategy, token, vault)
    genericStateOfVault(vault, token)


def test_emergency_exit(whale, token, vault, strategy, strategist, amount):
    # Deposit to the vault
    token.approve(vault, amount, {"from": whale})
    vault.deposit(amount, {"from": whale})
    strategy.harvest()

    # harvest should have transfered tokens to strat and staked it
    assert token.balanceOf(strategy) == 0

    # set emergency and exit
    strategy.setEmergencyExit()
    strategy.harvest()
    assert token.balanceOf(strategy) < amount


def test_change_debt(gov, whale, token, vault, strategy, strategist, amount):
    # Deposit to the vault and harvest
    token.approve(vault, amount, {"from": whale})
    vault.deposit(amount, {"from": whale})
    vault.updateStrategyDebtRatio(strategy, 5_000, {"from": gov})
    strategy.harvest()

    assert token.balanceOf(vault) == amount / 2

    vault.updateStrategyDebtRatio(strategy, 10_000, {"from": gov})
    strategy.harvest()
    assert strategy.balanceOfStake() >= amount
