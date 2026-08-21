const { ethers } = require("hardhat");

async function main() {
  const [deployer, keeper] = await ethers.getSigners();

  console.log("----------------------------------------------------");
  console.log("Deploying contracts with account:", deployer.address);
  console.log("Designated Keeper address:", keeper.address);
  console.log("----------------------------------------------------");

  const MockERC20 = await ethers.getContractFactory("MockERC20");
  const mockUSDC = await MockERC20.deploy("Mock USDC", "mUSDC", 6);
  await mockUSDC.waitForDeployment();
  const mockAddress = await mockUSDC.getAddress();
  console.log(`[+] MockERC20 deployed to: ${mockAddress}`);

  const Markov1Vault = await ethers.getContractFactory("Markov1Vault");
  const vault = await Markov1Vault.deploy(
    mockAddress,
    "Markov Vault Share",
    "mvUSDC",
    keeper.address
  );
  await vault.waitForDeployment();
  const vaultAddress = await vault.getAddress();
  console.log(`[+] Markov1Vault deployed to: ${vaultAddress}`);

  const seedAmount = ethers.parseUnits("100000", 6);
  await mockUSDC.mint(deployer.address, seedAmount);
  await mockUSDC.approve(vaultAddress, seedAmount);
  await vault.deposit(seedAmount, deployer.address);
  console.log(`[+] Vault seeded with 100,000 mUSDC. Total Assets: ${await vault.totalAssets()}`);
  console.log("----------------------------------------------------");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
