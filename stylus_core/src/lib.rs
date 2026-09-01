#![cfg_attr(not(any(test, feature = "export-abi")), no_main)]
#![cfg_attr(not(any(test, feature = "export-abi")), no_std)]

#[macro_use]
extern crate alloc;

use alloc::vec::Vec;
use stylus_sdk::{alloy_primitives::U256, prelude::*};

sol_storage! {
    #[entrypoint]
    pub struct DarkPoolIngestionCore {
        uint256 total_intents_parsed;
    }
}

#[public]
impl DarkPoolIngestionCore {
    pub fn parse_sbe_intent(&mut self, payload: Vec<u8>) -> Result<(U256, bool), Vec<u8>> {
        if payload.len() < 64 {
            return Err(b"Invalid SBE binary payload length".to_vec());
        }

        let mut pair_hash_bytes = [0u8; 32];
        pair_hash_bytes.copy_from_slice(&payload[0..32]);
        let pair_hash = U256::from_be_slice(&pair_hash_bytes);

        let is_buy = payload[48] == 1;

        let current = self.total_intents_parsed.get();
        self.total_intents_parsed.set(current + U256::from(1));

        Ok((pair_hash, is_buy))
    }

    pub fn get_total_intents(&self) -> Result<U256, Vec<u8>> {
        Ok(self.total_intents_parsed.get())
    }
}
