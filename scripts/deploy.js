const { ethers } = require("hardhat");

async function main() {
  const signers = await ethers.getSigners();
  const deployer = signers[0];
  const keeper = signers.length > 1 ? signers[1] : deployer;

  const deployerAddress = await deployer.getAddress();
  const keeperAddress = await keeper.getAddress();

  console.log("----------------------------------------------------");
  console.log("Deploying contracts with account:", deployerAddress);
  console.log("Designated Keeper address:", keeperAddress);
  console.log("----------------------------------------------------");

  // 1. Deploy Mock Asset (USDC)
  const MockERC20 = await ethers.getContractFactory("MockERC20");
  const mockUSDC = await MockERC20.deploy("Mock USDC", "mUSDC", 6);
  await mockUSDC.waitForDeployment();
  const mockAddress = await mockUSDC.getAddress();
  console.log(`[+] MockERC20 deployed to: ${mockAddress}`);

  // 2. Deploy Markov1Vault
  const Markov1Vault = await ethers.getContractFactory("Markov1Vault");
  const vault = await Markov1Vault.deploy(
    mockAddress,
    "Markov Vault Share",
    "mvUSDC",
    keeperAddress
  );
  await vault.waitForDeployment();
  const vaultAddress = await vault.getAddress();
  console.log(`[+] Markov1Vault deployed to: ${vaultAddress}`);

  // 3. Seed Vault with Initial Capital (100,000 mUSDC)
  const seedAmount = ethers.parseUnits("100000", 6);
  const mintTx = await mockUSDC.mint(deployerAddress, seedAmount);
  await mintTx.wait();

  const approveTx = await mockUSDC.approve(vaultAddress, seedAmount);
  await approveTx.wait();

  const depositTx = await vault.deposit(seedAmount, deployerAddress);
  await depositTx.wait();

  console.log(`[+] Vault seeded with 100,000 mUSDC. Total Assets: ${await vault.totalAssets()}`);
  console.log("----------------------------------------------------");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
