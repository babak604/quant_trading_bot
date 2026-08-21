const { ethers } = require("hardhat");

async function main() {
  const [deployer] = await ethers.getSigners();

  console.log("====================================================");
  console.log("Deploying to Arbitrum Sepolia");
  console.log("Deployer / Keeper Address:", deployer.address);

  const balance = await ethers.provider.getBalance(deployer.address);
  console.log("Account Balance:", ethers.formatEther(balance), "ETH");
  console.log("====================================================");

  if (balance === 0n) {
    throw new Error("[!] Deployer account has 0 Arbitrum Sepolia ETH. Fund account before continuing.");
  }

  // 1. Deploy Mock USDC for staging
  console.log("[1/3] Deploying MockERC20 (mUSDC)...");
  const MockERC20 = await ethers.getContractFactory("MockERC20");
  const mockUSDC = await MockERC20.deploy("Mock USDC", "mUSDC", 6);
  await mockUSDC.waitForDeployment();
  const mockAddress = await mockUSDC.getAddress();
  console.log("      MockERC20 Deployed:", mockAddress);

  // 2. Deploy Markov1Vault
  console.log("[2/3] Deploying Markov1Vault...");
  const name = "Markov Vault Share";
  const symbol = "mvUSDC";
  const keeperAddress = deployer.address;

  const Markov1Vault = await ethers.getContractFactory("Markov1Vault");
  const vault = await Markov1Vault.deploy(mockAddress, name, symbol, keeperAddress);
  await vault.waitForDeployment();
  const vaultAddress = await vault.getAddress();
  console.log("      Markov1Vault Deployed:", vaultAddress);

  // 3. Wait for block confirmations before verification
  console.log("[3/3] Waiting 5 block confirmations for Arbiscan indexing...");
  await vault.deploymentTransaction().wait(5);

  console.log("\n[+] Verification Command:");
  console.log(`npx hardhat verify --network arbitrumSepolia ${vaultAddress} "${mockAddress}" "${name}" "${symbol}" "${keeperAddress}"`);
  console.log("====================================================");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
