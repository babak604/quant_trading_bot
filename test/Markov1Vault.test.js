const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("Markov1Vault - Trade Execution Gate & Risk Sizing", function () {
  let vault, mockAsset;
  let owner, keeper, user;

  const INITIAL_DEPOSIT = ethers.parseUnits("100000", 6); // 100,000 USDC
  const SYMBOL = "BTC/USD";
  const REGIME = "BULL_ACCUMULATION";

  beforeEach(async function () {
    [owner, keeper, user] = await ethers.getSigners();

    // Deploy Mock ERC20 Token (6 decimals)
    const MockERC20 = await ethers.getContractFactory("MockERC20");
    mockAsset = await MockERC20.deploy("Mock USDC", "mUSDC", 6);
    await mockAsset.waitForDeployment();
    const assetAddress = await mockAsset.getAddress();

    // Deploy Markov1Vault
    const Markov1Vault = await ethers.getContractFactory("Markov1Vault");
    vault = await Markov1Vault.deploy(
      assetAddress,
      "Markov Vault Share",
      "mvUSDC",
      keeper.address
    );
    await vault.waitForDeployment();
    const vaultAddress = await vault.getAddress();

    // Seed vault with capital
    await mockAsset.mint(user.address, INITIAL_DEPOSIT);
    await mockAsset.connect(user).approve(vaultAddress, INITIAL_DEPOSIT);
    await vault.connect(user).deposit(INITIAL_DEPOSIT, user.address);
  });

  describe("Markov Regime Execution Gate", function () {
    it("Should REVERT trade execution if win probability is below 54.0% (5400 BPS)", async function () {
      const lowWinProb = 5399n;

      await expect(
        vault.connect(keeper).executeQuantSignal(SYMBOL, REGIME, lowWinProb)
      ).to.be.revertedWith("Markov1Vault: Win probability below 54.0% gate");
    });

    it("Should ALLOW trade execution when win probability is equal to 54.0% (5400 BPS)", async function () {
      const validWinProb = 5400n;
      const expectedAllocation = (INITIAL_DEPOSIT * 250n) / 10000n; // 2.5% = 2,500 USDC

      await expect(
        vault.connect(keeper).executeQuantSignal(SYMBOL, REGIME, validWinProb)
      )
        .to.emit(vault, "TradeExecuted")
        .withArgs(SYMBOL, REGIME, validWinProb, expectedAllocation);
    });
  });

  describe("Position Risk Sizing Controls (2.5% Cap)", function () {
    it("Should compute correct position allocation (2.5% of totalAssets)", async function () {
      const validWinProb = 6000n; // 60.0%
      const expectedAllocation = (INITIAL_DEPOSIT * 250n) / 10000n; // 2,500 USDC

      const tradeAllocation = await vault
        .connect(keeper)
        .executeQuantSignal.staticCall(SYMBOL, REGIME, validWinProb);

      expect(tradeAllocation).to.equal(expectedAllocation);
    });
  });

  describe("Access Controls", function () {
    it("Should REVERT if a non-keeper address attempts execution", async function () {
      const validWinProb = 6000n;

      await expect(
        vault.connect(user).executeQuantSignal(SYMBOL, REGIME, validWinProb)
      ).to.be.reverted;
    });
  });
});
