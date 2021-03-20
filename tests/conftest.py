import pytest
from brownie import config, Contract


@pytest.fixture
def gov(accounts):
    yield accounts[0]


@pytest.fixture
def rewards(accounts):
    yield accounts[1]

@pytest.fixture
def whale(accounts):
    # big binance7 wallet
    # acc = accounts.at('0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8', force=True)
    # big binance8 wallet
    acc = accounts.at("0xBa37B002AbaFDd8E89a1995dA52740bbC013D992", force=True)

    # lots of weth account
    #wethAcc = accounts.at("0x767Ecb395def19Ab8d1b2FCc89B3DDfBeD28fD6b", force=True)
    #weth.approve(acc, 2 ** 256 - 1, {"from": wethAcc})
    #weth.transfer(acc, weth.balanceOf(wethAcc), {"from": wethAcc})

    #assert weth.balanceOf(acc) > 0
    yield acc


@pytest.fixture
def yfi(interface):
    yield interface.ERC20("0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e")


@pytest.fixture
def router():
    yield Contract("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")

@pytest.fixture
def bank(interface):
    yield interface.ERC20("0x24A6A37576377F63f194Caa5F518a60f45b42921")

@pytest.fixture
def yfibank(interface,accounts,bank):
    yfibankPool = interface.ISynthetixRewards("0x90D1d83FD4CCa873848D728FD8CEf382b1aCB4B8")
    #we want to emulate this acc to get some bank to reallocate to yfi pool
    bankSource = accounts.at("0x8F2528EE4878c70C82d15903aE9f042A09E9D8F7", force=True)
    bankMs = accounts.at("0x383dF49ad1f0219759a46399fE33Cb7A63cd051c", force=True)
    amount = 20 * 10 ** 18
    #tranfer 10k bank to yfibank pool
    bank.transfer(yfibankPool,amount,{"from" : bankSource})
    #init rewards and start
    yfibankPool.notifyRewardAmount(amount,{"from" : bankMs})
    # return back the pool
    yield yfibankPool

@pytest.fixture
def pid():
    yield 8

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
def token(yfi):
    yield yfi


@pytest.fixture
def amount(accounts, token):
    amount = 1 * 10 ** token.decimals()
    # In order to get some funds for the token you are about to use,
    # it impersonate an exchange address to use it's funds.
    reserve = accounts.at("0x3ff33d9162aD47660083D7DC4bC02Fb231c81677", force=True)
    token.transfer(accounts[0], amount, {"from": reserve})
    yield amount


@pytest.fixture
def weth():
    token_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    yield Contract(token_address)


@pytest.fixture
def weth_amout(gov, weth):
    weth_amout = 10 ** weth.decimals()
    gov.transfer(weth, weth_amout)
    yield weth_amout
@pytest.fixture
def live_vault(pm, gov, rewards, guardian, management, token):
    Vault = pm(config["dependencies"][0]).Vault
    yield Vault.at('0xE14d13d8B3b85aF791b2AADD661cDBd5E6097Db1')

@pytest.fixture
def live_strat(Strategy):
    yield Strategy.at('0xd4419DDc50170CB2DBb0c5B4bBB6141F3bCc923B')

@pytest.fixture
def live_vault_weth(pm, gov, rewards, guardian, management, token):
    Vault = pm(config["dependencies"][0]).Vault
    yield Vault.at('0xa9fE4601811213c340e850ea305481afF02f5b28')

@pytest.fixture
def live_strat_weth(Strategy):
    yield Strategy.at('0xDdf11AEB5Ce1E91CF19C7E2374B0F7A88803eF36')

@pytest.fixture
def vault(pm, gov, rewards, guardian, management, token):
    Vault = pm(config["dependencies"][0]).Vault
    vault = guardian.deploy(Vault)
    vault.initialize(token, gov, rewards, "", "", guardian)
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    vault.setManagement(management, {"from": gov})
    yield vault


@pytest.fixture
def strategy(strategist, keeper, vault, Strategy, gov, yfibank, bank, router):
    strategy = strategist.deploy(Strategy, vault, yfibank, router, yfi, bank)
    strategy.setKeeper(keeper)

    vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 1_000, {"from": gov})
    yield strategy
