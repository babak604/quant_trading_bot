// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/extensions/ERC4626.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

contract QuantVault is ERC4626, AccessControl, ReentrancyGuard {
    bytes32 public constant KEEPER_ROLE = keccak256("KEEPER_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    bool public paused;
    
    string public currentRegime;
    uint256 public currentWinProbBps;

    event Rebalanced(string symbol, string regime, uint256 winProbBps, uint256 timestamp);
    event EmergencyPauseToggled(bool isPaused);

    modifier whenNotPaused() {
        require(!paused, "Vault: Paused");
        _;
    }

    constructor(
        IERC20 asset_,
        string memory name_,
        string memory symbol_,
        address admin_,
        address keeper_
    ) ERC4626(asset_) ERC20(name_, symbol_) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin_);
        _grantRole(PAUSER_ROLE, admin_);
        _grantRole(KEEPER_ROLE, keeper_);
    }

    function rebalance(
        string calldata symbol,
        string calldata regime,
        uint256 winProbBps
    ) external onlyRole(KEEPER_ROLE) whenNotPaused nonReentrant {
        currentRegime = regime;
        currentWinProbBps = winProbBps;

        emit Rebalanced(symbol, regime, winProbBps, block.timestamp);
    }

    function togglePause() external onlyRole(PAUSER_ROLE) {
        paused = !paused;
        emit EmergencyPauseToggled(paused);
    }

    function deposit(uint256 assets, address receiver) public override whenNotPaused returns (uint256) {
        return super.deposit(assets, receiver);
    }

    function withdraw(uint256 assets, address receiver, address owner) public override whenNotPaused returns (uint256) {
        return super.withdraw(assets, receiver, owner);
    }
}
