const hre = require("hardhat");

async function main() {
  const vault = await hre.ethers.getContractAt("Markov1Vault", process.env.MARKOV1_VAULT_ADDRESS);
  const [signer] = await hre.ethers.getSigners();
  const shares = await vault.balanceOf(signer.address);
  console.log(`🎟️ Vault Shares (mvUSDC): ${hre.ethers.formatUnits(shares, 6)}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
