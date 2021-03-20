// SPDX-License-Identifier: AGPL-3.0
// Feel free to change the license, but this is what we use

// Feel free to change this version of Solidity. We support >=0.6.0 <0.7.0;
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

interface SynthetixRewards {
    function stake(uint256 amount) external;
    function exit() external;
    function withdraw(uint256 amount) external;
    function getReward() external;
    function earned(address account) external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function stakeToken() external view returns (address);
    function rewardToken() external view returns (address);
}

// These are the core Yearn libraries
import "@yearnvaults/contracts/BaseStrategy.sol";
import {SafeERC20, SafeMath, IERC20, Address} from "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";
import "@openzeppelin/contracts/math/Math.sol";

import "./interfaces/UniswapInterfaces/IUniswapV2Router02.sol";

contract Strategy is BaseStrategy {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    address public staker;
    address public reward;

    address private constant uniswapRouter =
        address(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D);
    address private constant sushiswapRouter =
        address(0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F);
    address private constant weth =
        address(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2);

    address public router;


    address[] public path;

    event Cloned(address indexed clone);

    constructor(
        address _vault,
        address _staker,
        address _router
    ) public BaseStrategy(_vault) {
        //By default get data from the staker
        _initializeStrat(_staker, _router,address(0),address(0));
    }

    function initialize(
        address _vault,
        address _strategist,
        address _rewards,
        address _keeper,
        address _staker,
        address _router,
        address _want,
        address _reward
    ) external {
        //note: initialise can only be called once. in _initialize in BaseStrategy we have: require(address(want) == address(0), "Strategy already initialized");
        _initialize(_vault, _strategist, _rewards, _keeper);
        _initializeStrat(_staker, _router, _want, _reward);
    }

    function _initializeStrat(
        address _staker,
        address _router,
        address _want,
        address _reward
    ) internal {
        require(
            router == address(0),
            "Masterchef Strategy already initialized"
        );
        require(
            _router == uniswapRouter || _router == sushiswapRouter,
            "incorrect router"
        );

        // You can set these parameters on deployment to whatever you want
        maxReportDelay = 6300;
        profitFactor = 1500;
        debtThreshold = 1_000_000 * 1e18;
        staker = _staker;
        reward = _reward == address(0) ? SynthetixRewards(staker).rewardToken() : _reward;
        router = _router;

        require(address(want) == (_want == address(0) ? SynthetixRewards(staker).stakeToken() : _want) , "wrong want");

        want.safeApprove(_staker, uint256(-1));
        IERC20(reward).safeApprove(router, uint256(-1));
        path = getTokenOutPath(reward, address(want));
    }

    function cloneStrategy(
        address _vault,
        address _staker,
        address _router
    ) external returns (address newStrategy) {
        newStrategy = this.cloneStrategy(
            _vault,
            msg.sender,
            msg.sender,
            msg.sender,
            _staker,
            _router,
            address(0),
            address(0)
        );
    }

    function cloneStrategy(
        address _vault,
        address _staker,
        address _router,
        address _want,
        address _reward
    ) external returns (address newStrategy) {
        newStrategy = this.cloneStrategy(
            _vault,
            msg.sender,
            msg.sender,
            msg.sender,
            _staker,
            _router,
            _want,
            _reward
        );
    }

    function cloneStrategy(
        address _vault,
        address _strategist,
        address _rewards,
        address _keeper,
        address _staker,
        address _router,
        address _want,
        address _reward
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

        Strategy(newStrategy).initialize(
            _vault,
            _strategist,
            _rewards,
            _keeper,
            _staker,
            _router,
            _want,
            _reward
        );

        emit Cloned(newStrategy);
    }

    function setRouter(address _router)
        public
        onlyAuthorized
    {
        require(
            _router == uniswapRouter || _router == sushiswapRouter,
            "incorrect router"
        );

        //Revoke approval to old router
        IERC20(reward).safeApprove(router,0);
        router = _router;
        //Approve on new router
        IERC20(reward).safeApprove(router, uint256(-1));
    }

    function setPath(address[] calldata _path)
        public
        onlyGovernance
    {
        path = _path;

    }

    // ******** OVERRIDE THESE METHODS FROM BASE CONTRACT ************

    function name() external view override returns (string memory) {
        return "StrategySynthetixRewardsGeneric";
    }

    function pendingReward() public view returns (uint256) {
        return SynthetixRewards(staker).earned(address(this));
    }

    function balanceOfStake() public view returns (uint256) {
        return SynthetixRewards(staker).balanceOf(address(this));
    }

    function estimatedTotalAssets() public view override returns (uint256) {
        return want.balanceOf(address(this)).add(balanceOfStake());
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
        SynthetixRewards(staker).getReward();

        _sell();

        uint256 assets = estimatedTotalAssets();
        uint256 wantBal = want.balanceOf(address(this));

        uint256 debt = vault.strategies(address(this)).totalDebt;

        if (assets > debt) {
            _debtPayment = _debtOutstanding;
            _profit = assets - debt;

            uint256 amountToFree = _profit.add(_debtPayment);

            if (amountToFree > 0 && wantBal < amountToFree) {
                liquidatePosition(amountToFree);

                uint256 newLoose = want.balanceOf(address(this));

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

        uint256 wantBalance = want.balanceOf(address(this));
        SynthetixRewards(staker).stake(wantBalance);
    }

    function liquidatePosition(uint256 _amountNeeded)
        internal
        override
        returns (uint256 _liquidatedAmount, uint256 _loss)
    {
        uint256 totalAssets = want.balanceOf(address(this));
        if (_amountNeeded > totalAssets) {
            uint256 amountToFree = _amountNeeded.sub(totalAssets);

            uint256 deposited = balanceOfStake();
            if (deposited < amountToFree) {
                amountToFree = deposited;
            }
            if (deposited > 0) {
                SynthetixRewards(staker).withdraw(amountToFree);
            }

            _liquidatedAmount = want.balanceOf(address(this));
        } else {
            _liquidatedAmount = _amountNeeded;
        }
    }

    // NOTE: Can override `tendTrigger` and `harvestTrigger` if necessary

    function prepareMigration(address _newStrategy) internal override {
        liquidatePosition(uint256(-1)); //withdraw all. does not matter if we ask for too much
        _sell();
    }

    function emergencyWithdrawal(uint256 _pid) external  onlyGovernance {
        SynthetixRewards(staker).exit();
    }

    function getTokenOutPath(address _token_in,address _token_out ) internal view returns (address [] memory _path) {
        bool is_weth = _token_in == address(weth) || _token_out == address(weth);
        _path = new address[](is_weth ? 2 : 3);
        _path[0] = _token_in;
        if (is_weth) {
            _path[1] = _token_out;
        } else {
            _path[1] = address(weth);
            _path[2] = _token_out;
        }
    }

    //sell all function
    function _sell() internal {
        uint256 rewardBal = IERC20(reward).balanceOf(address(this));
        if( rewardBal == 0){
            return;
        }
        if(path.length == 0){
            IUniswapV2Router02(router).swapExactTokensForTokens(rewardBal, uint256(0), getTokenOutPath(reward,address(want)), address(this), now);
        }else{
            IUniswapV2Router02(router).swapExactTokensForTokens(rewardBal, uint256(0), path, address(this), now);
        }
    }

    function protectedTokens()
        internal
        view
        override
        returns (address[] memory)
    {}
}
