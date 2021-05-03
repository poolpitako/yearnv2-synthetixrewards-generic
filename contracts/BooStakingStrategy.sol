// SPDX-License-Identifier: AGPL-3.0
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

// These are the core Yearn libraries
import "@yearnvaults/contracts/BaseStrategy.sol";
import {
    SafeERC20,
    SafeMath,
    IERC20,
    Address
} from "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";
import "@openzeppelin/contracts/math/Math.sol";
import "./interfaces/IBooRewards.sol";

contract BooStakingStrategy is BaseStrategy {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    uint256 public pid;
    address public booRewards;

    event Cloned(address indexed clone);

    constructor(
        address _vault,
        address _booRewards,
        uint256 _pid
    ) public BaseStrategy(_vault) {
        _initializeStrat(_booRewards, _pid);
    }

    function initialize(
        address _vault,
        address _strategist,
        address _rewards,
        address _keeper,
        address _booRewards,
        uint256 _pid
    ) external {
        //note: initialise can only be called once. in _initialize in BaseStrategy
        // we have: require(address(want) == address(0), "Strategy already initialized");
        _initialize(_vault, _strategist, _rewards, _keeper);
        _initializeStrat(_booRewards, _pid);
    }

    function _initializeStrat(address _booRewards, uint256 _pid) internal {
        require(booRewards == address(0), "Strategy already initialized");

        // You can set these parameters on deployment to whatever you want
        maxReportDelay = 6300;
        profitFactor = 1500;
        debtThreshold = 1_000_000 * 1e18;
        booRewards = _booRewards;
        pid = _pid;

        want.safeApprove(booRewards, type(uint256).max);
    }

    function cloneStrategy(
        address _vault,
        address _strategist,
        address _rewards,
        address _keeper,
        address _booRewards,
        uint256 _pid
    ) external returns (address newStrategy) {
        // Copied from https://github.com/optionality/clone-factory/blob/master/contracts/CloneFactory.sol
        bytes20 addressBytes = bytes20(address(this));

        assembly {
            // EIP-1167 bytecode
            let clone_code := mload(0x40)
            mstore(
                clone_code,
                0x3d602d80600a3d3981f3363d3d373d3d3d363d73000000000000000000000000
            )
            mstore(add(clone_code, 0x14), addressBytes)
            mstore(
                add(clone_code, 0x28),
                0x5af43d82803e903d91602b57fd5bf30000000000000000000000000000000000
            )
            newStrategy := create(0, clone_code, 0x37)
        }

        BooStakingStrategy(newStrategy).initialize(
            _vault,
            _strategist,
            _rewards,
            _keeper,
            _booRewards,
            _pid
        );

        emit Cloned(newStrategy);
    }

    // ******** OVERRIDE THESE METHODS FROM BASE CONTRACT ************

    function name() external view override returns (string memory) {
        return "StrategyBooStakingRewards";
    }

    function pendingReward() public view returns (uint256) {
        return IBooRewards(booRewards).pendingBOO(pid, address(this));
    }

    function balanceOfWant() public view returns (uint256) {
        return want.balanceOf(address(this));
    }

    function balanceOfStake() public view returns (uint256) {
        return IBooRewards(booRewards).userInfo(pid, address(this)).amount;
    }

    function estimatedTotalAssets() public view override returns (uint256) {
        return balanceOfWant().add(balanceOfStake());
    }

    function prepareReturn(uint256 _debtOutstanding)
        internal
        override
        returns (
            uint256 _profit,
            uint256 _loss,
            uint256 _debtPayment
        )
    {
        // Claim profit
        IBooRewards(booRewards).withdraw(pid, 0);

        uint256 assets = estimatedTotalAssets();
        uint256 wantBal = balanceOfWant();

        uint256 debt = vault.strategies(address(this)).totalDebt;

        if (assets >= debt) {
            _debtPayment = _debtOutstanding;
            _profit = assets - debt;

            uint256 amountToFree = _profit.add(_debtPayment);

            if (amountToFree > 0 && wantBal < amountToFree) {
                liquidatePosition(amountToFree);

                uint256 newLoose = balanceOfWant();

                //if we dont have enough money adjust _debtOutstanding and only change profit if needed
                if (newLoose < amountToFree) {
                    if (_profit > newLoose) {
                        _profit = newLoose;
                        _debtPayment = 0;
                    } else {
                        _debtPayment = Math.min(
                            newLoose - _profit,
                            _debtPayment
                        );
                    }
                }
            }
        } else {
            //serious loss should never happen but if it does lets record it accurately
            _loss = debt - assets;
        }
    }

    function adjustPosition(uint256 _debtOutstanding) internal override {
        if (emergencyExit) {
            return;
        }

        uint256 wantBalance = balanceOfWant();
        if (wantBalance > 0) {
            IBooRewards(booRewards).deposit(pid, wantBalance);
        }
    }

    function liquidatePosition(uint256 _amountNeeded)
        internal
        override
        returns (uint256 _liquidatedAmount, uint256 _loss)
    {
        uint256 totalAssets = balanceOfWant();
        if (_amountNeeded > totalAssets) {
            uint256 amountToFree = _amountNeeded.sub(totalAssets);
            uint256 deposited = balanceOfStake();

            // amountToFree can only go up to deposited amount
            if (deposited < amountToFree) {
                amountToFree = deposited;
            }

            if (deposited > 0 && amountToFree > 0) {
                IBooRewards(booRewards).withdraw(pid, amountToFree);
            }
        }

        uint256 wantBalance = balanceOfWant();
        if (wantBalance >= _amountNeeded) {
            _liquidatedAmount = _amountNeeded;
        } else {
            _liquidatedAmount = wantBalance;
            _loss = _amountNeeded.sub(wantBalance);
        }
    }

    function prepareMigration(address _newStrategy) internal override {
        //withdraw all. does not matter if we ask for too much
        liquidatePosition(type(uint256).max);
    }

    function protectedTokens()
        internal
        view
        override
        returns (address[] memory)
    {}
}
