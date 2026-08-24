// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IGMXVault {
    function deposit(address token, uint256 amount) external returns (uint256);
}

interface ICamelotRouter {
    function addLiquidity(
        address tokenA,
        address tokenB,
        uint256 amountADesired,
        uint256 amountBDesired,
        uint256 amountAMin,
        uint256 amountBMin,
        address to,
        uint256 deadline
    ) external returns (uint256 amountA, uint256 amountB, uint256 liquidity);
}

contract QuantVaultAdapter is AccessControl {
    bytes32 public constant STRATEGIST_ROLE = keccak256("STRATEGIST_ROLE");

    address public immutable usdc;
    address public gmxPool;
    address public camelotRouter;

    enum AllocationStrategy { CASH, GMX_YIELD, CAMELOT_DEX }
    AllocationStrategy public currentStrategy;

    event StrategyShifted(AllocationStrategy indexed newStrategy, uint256 timestamp);

    constructor(address _usdc, address _gmxPool, address _camelotRouter) {
        usdc = _usdc;
        gmxPool = _gmxPool;
        camelotRouter = _camelotRouter;
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(STRATEGIST_ROLE, msg.sender);
        currentStrategy = AllocationStrategy.CASH;
    }

    function executeStrategyShift(string memory regime, uint256 winProbBps) external onlyRole(STRATEGIST_ROLE) {
        if (winProbBps >= 8000) {
            currentStrategy = AllocationStrategy.CAMELOT_DEX;
        } else if (winProbBps >= 5000) {
            currentStrategy = AllocationStrategy.GMX_YIELD;
        } else {
            currentStrategy = AllocationStrategy.CASH;
        }
        emit StrategyShifted(currentStrategy, block.timestamp);
    }
}
