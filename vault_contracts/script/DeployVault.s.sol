// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/QuantVault.sol";

contract DeployVault is Script {
    function run() external {
        address mockUsdc = 0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d; // Sepolia USDC

        vm.startBroadcast();

        QuantVault vault = new QuantVault(
            IERC20(mockUsdc),
            "Quant Vault USDC",
            "vUSDC",
            msg.sender,
            msg.sender
        );

        console.log("--------------------------------------------------");
        console.log("QuantVault ERC-4626 Deployed To:", address(vault));
        console.log("--------------------------------------------------");

        vm.stopBroadcast();
    }
}
