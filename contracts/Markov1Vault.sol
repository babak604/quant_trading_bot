// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC20/extensions/ERC4626.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

contract Markov1Vault is ERC4626, Ownable, ReentrancyGuard, Pausable {
    
    address public keeperNode;
    uint256 public performanceFeeBps = 1500; // 15.0%
    uint256 public constant BPS_DENOMINATOR = 10000;
    
    uint256 public maxPositionRiskBps = 250; // 2.5%
    uint256 public minWinProbThreshold = 5400; // 54.0%
    
    event TradeExecuted(string symbol, string regime, uint256 winProb, uint256 allocatedAmount);
    event KeeperUpdated(address indexed oldKeeper, address indexed newKeeper);
    event PerformanceFeeUpdated(uint256 newFeeBps);
    event EmergencyPaused(address indexed owner);
    event EmergencyUnpaused(address indexed owner);

    modifier onlyKeeper() {
        require(msg.sender == keeperNode, "Markov1Vault: Caller is not the authorized Keeper");
        _;
    }

    constructor(
        IERC20 asset_,
        string memory name_,
        string memory symbol_,
        address keeperNode_
    ) ERC4626(asset_) ERC20(name_, symbol_) Ownable(msg.sender) {
        require(keeperNode_ != address(0), "Invalid keeper address");
        keeperNode = keeperNode_;
    }

    function pauseVault() external onlyOwner {
        _pause();
        emit EmergencyPaused(msg.sender);
    }

    function unpauseVault() external onlyOwner {
        _unpause();
        emit EmergencyUnpaused(msg.sender);
    }

    function executeQuantSignal(
        string calldata symbol,
        string calldata regime,
        uint256 winProb
    ) external onlyKeeper nonReentrant whenNotPaused returns (uint256 tradeAllocation) {
        require(winProb >= minWinProbThreshold, "Markov1Vault: Win probability below 54.0% gate");

        uint256 totalVaultCapital = totalAssets();
        tradeAllocation = (totalVaultCapital * maxPositionRiskBps) / BPS_DENOMINATOR;

        emit TradeExecuted(symbol, regime, winProb, tradeAllocation);
        return tradeAllocation;
    }

    function setKeeperNode(address newKeeper) external onlyOwner {
        require(newKeeper != address(0), "Invalid address");
        emit KeeperUpdated(keeperNode, newKeeper);
        keeperNode = newKeeper;
    }

    function setPerformanceFee(uint256 newFeeBps) external onlyOwner {
        require(newFeeBps <= 3000, "Fee cannot exceed 30%");
        performanceFeeBps = newFeeBps;
        emit PerformanceFeeUpdated(newFeeBps);
    }
}
