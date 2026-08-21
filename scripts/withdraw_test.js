const hre = require("hardhat");

async function main() {
  const vaultAddress = process.env.MARKOV1_VAULT_ADDRESS;
  const usdcAddress = "0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d";
  const [deployer] = await hre.ethers.getSigners();

  const usdcAbi = [
    "function balanceOf(address account) external view returns (uint256)"
  ];
  
  const usdc = new hre.ethers.Contract(usdcAddress, usdcAbi, deployer);
  const vault = await hre.ethers.getContractAt("Markov1Vault", vaultAddress);

  // 1. Check share balance before withdrawal
  const sharesBefore = await vault.balanceOf(deployer.address);
  console.log(`🎟️ Starting Vault Shares: ${hre.ethers.formatUnits(sharesBefore, 6)} mvUSDC`);

  if (sharesBefore === 0n) {
    console.log("⚠️ No shares available to redeem.");
    return;
  }

  // 2. Redeem 0.5 mvUSDC for underlying USDC
  const redeemAmount = hre.ethers.parseUnits("0.5", 6);
  console.log("⏳ Redeeming 0.5 mvUSDC shares...");
  const redeemTx = await vault.redeem(redeemAmount, deployer.address, deployer.address);
  await redeemTx.wait();
  console.log("✅ Redemption confirmed!");

  // 3. Print updated wallet balances and vault TVL
  const sharesAfter = await vault.balanceOf(deployer.address);
  const walletUsdc = await usdc.balanceOf(deployer.address);
  const totalAssets = await vault.totalAssets();

  console.log("==================================================");
  console.log(`🎟️ Remaining Shares:    ${hre.ethers.formatUnits(sharesAfter, 6)} mvUSDC`);
  console.log(`💼 Wallet USDC Balance:  ${hre.ethers.formatUnits(walletUsdc, 6)} USDC`);
  console.log(`🏦 Vault Total Assets:  ${hre.ethers.formatUnits(totalAssets, 6)} USDC`);
  console.log("==================================================");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
