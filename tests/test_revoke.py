def test_revoke_strategy_from_vault(token, vault, strategy, amount, gov, whale):
    # Deposit to the vault and harvest
    token.approve(vault, amount, {"from": whale})
    vault.deposit(amount, {"from": whale})
    strategy.harvest()
    assert token.balanceOf(strategy) == 0

    vault.revokeStrategy(strategy, {"from": gov})
    strategy.harvest()
    assert token.balanceOf(vault) >= amount
