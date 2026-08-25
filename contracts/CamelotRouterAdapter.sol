// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IMarkovStylusEngine {
    function get_regime() external view returns (uint256);
    function get_win_prob() external view returns (uint256);
}

interface ICamelotV3SwapRouter {
    struct ExactInputSingleParams {
        address tokenIn;
        address tokenOut;
        address recipient;
        uint256 deadline;
        uint256 amountIn;
        uint256 amountOutMinimum;
        uint160 limitSqrtPrice;
    }
    function exactInputSingle(ExactInputSingleParams calldata params) external returns (uint256 amountOut);
}

contract CamelotRouterAdapter is Ownable {
    IMarkovStylusEngine public immutable stylusEngine;
    ICamelotV3SwapRouter public immutable camelotRouter;
    IERC20 public immutable morUSD;

    event StrategyExecuted(uint256 regime, uint256 winProbBps, uint256 amountIn, uint256 amountOut);

    constructor(address _stylusEngine, address _camelotRouter, address _morUSD) Ownable(msg.sender) {
        stylusEngine = IMarkovStylusEngine(_stylusEngine);
        camelotRouter = ICamelotV3SwapRouter(_camelotRouter);
        morUSD = IERC20(_morUSD);
    }

    function rebalance(
        address tokenOut,
        uint256 amountIn,
        uint256 minAmountOut
    ) external onlyOwner returns (uint256 amountOut) {
        uint256 regime = stylusEngine.get_regime();
        uint256 winProb = stylusEngine.get_win_prob();

        require(regime >= 1 && winProb > 5500, "Signal conditions not met");

        morUSD.transferFrom(msg.sender, address(this), amountIn);
        morUSD.approve(address(camelotRouter), amountIn);

        ICamelotV3SwapRouter.ExactInputSingleParams memory params = ICamelotV3SwapRouter.ExactInputSingleParams({
            tokenIn: address(morUSD),
            tokenOut: tokenOut,
            recipient: msg.sender,
            deadline: block.timestamp + 300,
            amountIn: amountIn,
            amountOutMinimum: minAmountOut,
            limitSqrtPrice: 0
        });

        amountOut = camelotRouter.exactInputSingle(params);
        emit StrategyExecuted(regime, winProb, amountIn, amountOut);
    }
}
