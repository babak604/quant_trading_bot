#![no_std]
extern crate alloc;

use alloc::vec::Vec;
use stylus_sdk::{
    alloy_primitives::{Address, U256, FixedBytes},
    msg,
    prelude::*,
    storage::{StorageAddress, StorageBool, StorageMap, StorageU256},
};

#[global_allocator]
static ALLOC: mini_alloc::MiniAlloc = mini_alloc::MiniAlloc::INIT;

sol_storage! {
    #[entrypoint]
    pub struct MorMoneyEngine {
        StorageAddress owner;
        StorageMap<Address, StorageBool> session_key_whitelists;
        StorageMap<FixedBytes<32>, StorageU256> order_commitments;
        StorageMap<FixedBytes<32>, StorageBool> verified_zkml_image_ids;
    }
}

#[public]
impl MorMoneyEngine {
    pub fn init(&mut self) -> Result<(), Vec<u8>> {
        if self.owner.get() == Address::ZERO {
            self.owner.set(msg::sender());
        }
        Ok(())
    }

    pub fn set_session_key(&mut self, agent: Address, allowed: bool) -> Result<(), Vec<u8>> {
        if msg::sender() != self.owner.get() {
            return Err(alloc::format!("Unauthorized call").into_bytes());
        }
        self.session_key_whitelists.setter(agent).set(allowed);
        Ok(())
    }

    pub fn register_zkml_model(&mut self, image_id: FixedBytes<32>) -> Result<(), Vec<u8>> {
        if msg::sender() != self.owner.get() {
            return Err(alloc::format!("Unauthorized call").into_bytes());
        }
        self.verified_zkml_image_ids.setter(image_id).set(true);
        Ok(())
    }

    pub fn execute_agent_intent(
        &mut self,
        _target_venue: Address,
        max_slippage_bps: U256,
        zkml_image_id: FixedBytes<32>,
    ) -> Result<bool, Vec<u8>> {
        let sender = msg::sender();
        
        if !self.session_key_whitelists.get(sender) {
            return Err(alloc::format!("Unauthorized ERC-7579 Agent Session Key").into_bytes());
        }

        if !self.verified_zkml_image_ids.get(zkml_image_id) {
            return Err(alloc::format!("Unregistered zkML Model Image ID").into_bytes());
        }

        if max_slippage_bps > U256::from(30) {
            return Err(alloc::format!("Intent execution exceeds 30 bps limit").into_bytes());
        }

        Ok(true)
    }
}
