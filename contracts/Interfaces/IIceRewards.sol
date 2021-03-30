// SPDX-License-Identifier: MIT
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

struct UserInfo {
    uint256 amount;
    uint256 rewardDebt;
    uint256 remainingIceTokenReward;
}

interface IIceRewards {
    struct UserInfo {
        uint256 amount; // How many LP tokens the user has provided.
        uint256 rewardDebt; // Reward debt. See explanation below.
        uint256 remainingIceTokenReward; // ICE Tokens that weren't distributed for user per pool.
    }

    function withdraw(uint256 _pid, uint256 _amount) external;

    function deposit(uint256 _pid, uint256 _amount) external;

    function pendingIce(uint256 _pid, address _user)
        external
        view
        returns (uint256);

    function userInfo(uint256 _pid, address _user)
        external
        view
        returns (UserInfo memory);
}
