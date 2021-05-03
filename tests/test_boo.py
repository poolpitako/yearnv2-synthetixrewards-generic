import brownie
from brownie import Contract, Wei, chain


def test_boo(
    boo,
    boo_vault,
    boo_strategy,
    strategist,
    boo_whale,
    gov,
    boo_rewards,
    boo_pid,
):

    prev_balance = boo.balanceOf(boo_whale)
    boo.approve(boo_vault, 2 ** 256 - 1, {"from": boo_whale})
    boo_vault.deposit(Wei("100 ether"), {"from": boo_whale})

    boo_strategy.harvest({"from": strategist})

    chain.sleep(60 * 60 * 24 * 30)
    chain.mine(1)

    boo_strategy.harvest({"from": strategist})
    chain.sleep(60 * 60 * 8)
    chain.mine(1)

    boo_vault.withdraw({"from": boo_whale})
    assert prev_balance < boo.balanceOf(boo_whale)
