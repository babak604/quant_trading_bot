const hre = require("hardhat");

async function main() {
  const vaultAddress = process.env.MARKOV1_VAULT_ADDRESS;
  // Official Circle USDC address on Arbitrum Sepolia
  const usdcAddress = "0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d"; 
  const [deployer] = await hre.ethers.getSigners();

  const usdcAbi = [
    "function approve(address spender, uint256 amount) external returns (bool)",
    "function balanceOf(address account) external view returns (uint256)"
  ];
  
  const usdc = new hre.ethers.Contract(usdcAddress, usdcAbi, deployer);
  const vault = await hre.ethers.getContractAt("Markov1Vault", vaultAddress);

  // 1. Check current testnet USDC balance
  const balance = await usdc.balanceOf(deployer.address);
  console.log(`💼 Wallet USDC Balance: ${hre.ethers.formatUnits(balance, 6)} USDC`);

  if (balance === 0n) {
    console.log("⚠️ No testnet USDC found. Request tokens from https://faucet.circle.com/");
    return;
  }

  // 2. Approve 1 USDC spend to the Vault
  const depositAmount = hre.ethers.parseUnits("1.0", 6);
  console.log("⏳ Approving Vault to spend 1 USDC...");
  const approveTx = await usdc.approve(vaultAddress, depositAmount);
  await approveTx.wait();
  console.log("✅ Approval confirmed!");

  // 3. Execute Deposit into Vault
  console.log("⏳ Depositing 1 USDC into Vault...");
  const depositTx = await vault.deposit(depositAmount, deployer.address);
  await depositTx.wait();
  console.log("🟢 Deposit successful!");

  // 4. Print updated Vault TVL
  const totalAssets = await vault.totalAssets();
  console.log(`🏦 Vault Total Assets: ${hre.ethers.formatUnits(totalAssets, 6)} USDC`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
