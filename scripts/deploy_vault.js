const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("==================================================");
  console.log("🚀 Deploying Markov1Vault with Account:", deployer.address);

  // Arbitrum Sepolia Testnet USDC Address
  const UNDERLYING_USDC = process.env.USDC_TOKEN_ADDRESS || "0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d"; 
  const KEEPER_ADDRESS = deployer.address;

  const Vault = await hre.ethers.getContractFactory("Markov1Vault");
  const vault = await Vault.deploy(
    UNDERLYING_USDC,
    "Markov-1 Yield Vault",
    "mvUSDC",
    KEEPER_ADDRESS
  );

  await vault.waitForDeployment();
  const vaultAddress = await vault.getAddress();

  console.log("🟢 Markov1Vault Deployed Successfully!");
  console.log("   • Contract Address:", vaultAddress);
  console.log("   • Underlying Asset:", UNDERLYING_USDC);
  console.log("   • Keeper Node:     ", KEEPER_ADDRESS);
  console.log("==================================================");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
