const hre = require("hardhat");

async function main() {
  const vaultAddress = process.env.MARKOV1_VAULT_ADDRESS;
  if (!vaultAddress) {
    throw new Error("Please set MARKOV1_VAULT_ADDRESS in your .env file!");
  }

  const vault = await hre.ethers.getContractAt("Markov1Vault", vaultAddress);
  
  const name = await vault.name();
  const symbol = await vault.symbol();
  const asset = await vault.asset();
  const totalAssets = await vault.totalAssets();

  console.log("==================================================");
  console.log(`Vault Name:    ${name} (${symbol})`);
  console.log(`Contract Addr: ${vaultAddress}`);
  console.log(`Underlying:    ${asset}`);
  console.log(`Total Assets:  ${totalAssets.toString()}`);
  console.log("==================================================");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
