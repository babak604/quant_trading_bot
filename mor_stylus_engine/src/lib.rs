#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::{
    alloy_primitives::{Address, U256},
    prelude::*,
    storage::{StorageAddress, StorageU256},
};

#[storage]
#[entrypoint]
pub struct MarkovStylusEngine {
    owner: StorageAddress,
    current_regime: StorageU256,
    win_prob_bps: StorageU256,
}

#[public]
impl MarkovStylusEngine {
    pub fn init(&mut self) {
        let caller = self.vm().msg_sender();
        self.owner.set(caller);
        self.current_regime.set(U256::from(1));   // 1 = Sideways
        self.win_prob_bps.set(U256::from(5000));  // 50.00%
    }

    pub fn update_signal(&mut self, regime: U256, win_prob_bps: U256) -> Result<(), Vec<u8>> {
        if self.vm().msg_sender() != self.owner.get() {
            return Err("Unauthorized: caller is not owner".as_bytes().to_vec());
        }
        self.current_regime.set(regime);
        self.win_prob_bps.set(win_prob_bps);
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
