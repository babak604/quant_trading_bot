# Automated On-Chain Strategy Keeper Service

An autonomous quantitative trading bot pipeline operating on Arbitrum Sepolia. The system polls local Markov signal predictions from SQLite and executes on-chain state updates through a Solidity vault contract using Web3.py and systemd.

## Core System Architecture

* **Blockchain Network:** Arbitrum Sepolia Testnet (Chain ID: `421614`)
* **Smart Contract:** `Markov1Vault.sol` (`solc 0.8.20`)
* **Active Vault Address:** `0x2181b1146c7B86ac3d95e9380988c69847CCbef8`
* **Execution Service:** `keeper.service` (Python 3.12, Web3.py, systemd)
* **Data Layer:** SQLite (`signals.db`)

## System Features

1. **EVM Compatibility & Solc Compilation:** Compiled using `py-solc-x` bindings to guarantee precise ABI alignment and EVM bytecode integrity.
2. **EIP-1559 Dynamic Fee Estimation:** Implements explicit `maxFeePerGas` and `maxPriorityFeePerGas` parameters to prevent transaction reverts under fluctuating block base fees.
3. **Revert Protection:** Pre-flight state simulation (`.call()`) and ownership checking prior to on-chain broadcast.
4. **Service Persistence:** Autonomous daemon execution managed by `systemd` with automatic restart policies.

## On-Chain Verification

* **Contract Owner:** `0xdf953218A73E7d804AdBc631034098990eB26B94`
* **Sample Transaction (Signal #48 Execution):** `0xfadb316e2ee3ff4e0ebf476451a3bded2911d78d73ed3dc94d2aa07dbdccf6`
