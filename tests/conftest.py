import pytest
from brownie import config, Contract, Wei


@pytest.fixture
def gov(accounts):
    yield accounts[0]


@pytest.fixture
def rewards(accounts):
    yield accounts[1]


@pytest.fixture
def whale(accounts):
    yield accounts.at("0x5c82f157964de5bb292774e27ac331d1e647020b", force=True)


@pytest.fixture
def ice(interface):
    yield interface.ERC20("0xf16e81dce15b08f326220742020379b855b87df9")


@pytest.fixture
def boo(interface):
    yield interface.ERC20("0x841fad6eae12c286d1fd18d1d525dffa75c7effe")


@pytest.fixture
def boo_whale(accounts):
    yield accounts.at("0x95478c4f7d22d1048f46100001c2c69d2ba57380", force=True)


@pytest.fixture
def boo_pid():
    yield 0


@pytest.fixture
def pid():
    yield 0


@pytest.fixture
def guardian(accounts):
    yield accounts[2]


@pytest.fixture
def management(accounts):
    yield accounts[3]


@pytest.fixture
def strategist(accounts):
    yield accounts[4]


@pytest.fixture
def keeper(accounts):
    yield accounts[5]


@pytest.fixture
def token(ice):
    yield ice


@pytest.fixture
def ice_rewards(interface):
    yield interface.IIceRewards("0x05200cb2cee4b6144b2b2984e246b52bb1afcbd0")


@pytest.fixture
def boo_rewards(interface):
    yield interface.IBooRewards("0xACACa07e398d4946AD12232F40f255230e73Ca72")


@pytest.fixture
def amount():
    yield Wei("1000 ether")


@pytest.fixture
def boo_vault(pm, gov, rewards, guardian, management, boo):
    Vault = pm(config["dependencies"][0]).Vault
    vault = guardian.deploy(Vault)
    vault.initialize(boo, gov, rewards, "", "", guardian)
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    vault.setManagement(management, {"from": gov})
    yield vault


@pytest.fixture
def boo_strategy(
    strategist, boo_vault, BooStakingStrategy, boo, gov, boo_rewards, boo_pid
):
    strategy = strategist.deploy(BooStakingStrategy, boo_vault, boo_rewards, boo_pid)
    boo_vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 1_000, {"from": gov})
    yield strategy


@pytest.fixture
def vault(pm, gov, rewards, guardian, management, token):
    Vault = pm(config["dependencies"][0]).Vault
    vault = guardian.deploy(Vault)
    vault.initialize(token, gov, rewards, "", "", guardian)
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    vault.setManagement(management, {"from": gov})
    yield vault


@pytest.fixture
def strategy(strategist, keeper, vault, Strategy, token, gov, ice_rewards, pid):
    strategy = strategist.deploy(Strategy, vault, ice_rewards, pid)
    strategy.setKeeper(keeper)

    vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 1_000, {"from": gov})
    yield strategy
