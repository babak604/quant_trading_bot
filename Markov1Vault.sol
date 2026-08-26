
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Markov1Vault {
    address public owner;
    string public currentRegime;
    uint256 public currentWinProbBps;

    event StrategyStateUpdated(string regime, uint256 winProbBps);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function updateStrategyState(string calldata _regime, uint256 _winProbBps) external onlyOwner {
        currentRegime = _regime;
        currentWinProbBps = _winProbBps;
        emit StrategyStateUpdated(_regime, _winProbBps);
    }
}
