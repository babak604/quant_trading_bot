#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::{
    alloy_primitives::{Address, U256},
    prelude::*,
};

sol_storage! {
    #[entrypoint]
    pub struct MarkovStylusEngine {
        uint256 current_regime; // 0 = Bear, 1 = Sideways, 2 = Bull
        uint256 win_prob_bps;   // Basis points (e.g. 7500 = 75.00%)
        address owner;
    }
}

#[public]
impl MarkovStylusEngine {
    pub fn init(&mut self) {
        let sender = self.vm().msg_sender();
        self.owner.set(sender);
        self.current_regime.set(U256::from(1));  // Default Sideways
        self.win_prob_bps.set(U256::from(5000)); // Default 50%
    }

    pub fn update_signal(&mut self, new_regime: U256, new_win_prob_bps: U256) -> Result<(), Vec<u8>> {
        if self.vm().msg_sender() != self.owner.get() {
            return Err("Unauthorized owner caller".as_bytes().to_vec());
        }
        if new_regime > U256::from(2) {
            return Err("Invalid regime value".as_bytes().to_vec());
        }
        if new_win_prob_bps > U256::from(10000) {
            return Err("BPS exceeds 100%".as_bytes().to_vec());
        }

        self.current_regime.set(new_regime);
        self.win_prob_bps.set(new_win_prob_bps);
        Ok(())
    }

    pub fn get_regime(&self) -> U256 {
        self.current_regime.get()
    }

    pub fn get_win_prob(&self) -> U256 {
        self.win_prob_bps.get()
    }

    pub fn get_owner(&self) -> Address {
        self.owner.get()
    }
}
