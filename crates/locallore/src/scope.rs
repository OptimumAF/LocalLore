use crate::contracts::{Error, Scope};
use std::collections::{BTreeMap, BTreeSet};

/// Only explicit fork creation is supported. Untrusted lineage import is deliberately absent.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Lineage {
    story: String,
    parents: BTreeMap<String, Option<(String, u64)>>,
}

impl Lineage {
    pub fn new(scope: &Scope) -> Self {
        Self {
            story: scope.story.clone(),
            parents: [(scope.branch.clone(), None)].into(),
        }
    }

    pub fn fork(&mut self, parent: &Scope, child: &str, at: u64, head: u64) -> Result<(), Error> {
        if parent.story != self.story || !self.parents.contains_key(&parent.branch) {
            return Err(Error::Scope);
        }
        if child.is_empty() || child.len() > 64 || self.parents.contains_key(child) || at > head {
            return Err(Error::Rule);
        }
        // The small proof supports at most 32 ancestors; refuse before constructing deeper trees.
        let mut node = parent.branch.as_str();
        let mut depth = 1;
        while let Some(Some((ancestor, _))) = self.parents.get(node) {
            depth += 1;
            node = ancestor;
        }
        if depth >= 32 {
            return Err(Error::Rule);
        }
        self.parents
            .insert(child.into(), Some((parent.branch.clone(), at)));
        Ok(())
    }

    /// Scope/ancestry/time eligibility is evaluated before content is serialized for inference.
    pub fn eligible(&self, target: &Scope, head: u64, source: &Scope, sequence: u64) -> bool {
        if target.story != self.story || source.story != self.story || sequence == 0 {
            return false;
        }
        let mut node = target.branch.as_str();
        let mut cap = head;
        let mut seen = BTreeSet::new();
        for _ in 0..32 {
            if !seen.insert(node) {
                return false;
            }
            let Some(parent) = self.parents.get(node) else {
                return false;
            };
            if node == source.branch {
                return sequence <= cap;
            }
            match parent {
                Some((ancestor, fork)) => {
                    cap = cap.min(*fork);
                    node = ancestor;
                }
                None => return false,
            }
        }
        false
    }
}
