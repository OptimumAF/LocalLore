use crate::contracts::{Error, Scope};
use std::collections::{BTreeMap, BTreeSet};

/// Only explicit fork creation is supported. Untrusted lineage import is deliberately absent.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Lineage {
    story: String,
    parents: BTreeMap<String, Option<(String, u64)>>,
}

/// Private selected ancestry identity for derived coverage binding. Not a wire
/// grant, imported lineage, or enumeration of unrelated branches.
#[derive(Clone, Debug, PartialEq, Eq, serde::Serialize)]
pub(crate) struct LineageBindingEntry {
    pub branch: String,
    pub parent: Option<String>,
    pub fork_revision: Option<u64>,
}

impl Lineage {
    pub(crate) fn binding(&self, target: &Scope) -> Result<Vec<LineageBindingEntry>, Error> {
        if target.story != self.story {
            return Err(Error::Scope);
        }
        let mut node = target.branch.as_str();
        let mut seen = BTreeSet::new();
        let mut result = Vec::new();
        for _ in 0..32 {
            if !seen.insert(node) {
                return Err(Error::Scope);
            }
            let parent = self.parents.get(node).ok_or(Error::Scope)?;
            result.push(LineageBindingEntry {
                branch: node.to_owned(),
                parent: parent.as_ref().map(|(branch, _)| branch.clone()),
                fork_revision: parent.as_ref().map(|(_, revision)| *revision),
            });
            match parent {
                Some((branch, _)) => node = branch,
                None => return Ok(result),
            }
        }
        Err(Error::Scope)
    }
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

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn binding_preserves_prebirth_fork_chain_without_unselected_branches() {
        let root = Scope {
            story: "story".into(),
            branch: "root".into(),
        };
        let mut lineage = Lineage::new(&root);
        lineage.fork(&root, "a", 5, 5).unwrap();
        lineage.fork(&root, "unselected", 0, 5).unwrap();
        let a = Scope {
            story: "story".into(),
            branch: "a".into(),
        };
        lineage.fork(&a, "b", 1, 6).unwrap();
        let b = Scope {
            story: "story".into(),
            branch: "b".into(),
        };
        assert_eq!(
            serde_json::to_value(lineage.binding(&b).unwrap()).unwrap(),
            serde_json::json!([
                {"branch":"b","parent":"a","fork_revision":1},
                {"branch":"a","parent":"root","fork_revision":5},
                {"branch":"root","parent":null,"fork_revision":null}
            ])
        );
        assert_eq!(lineage.binding(&root).unwrap().len(), 1);
        assert_eq!(
            lineage
                .binding(&Scope {
                    story: "other".into(),
                    branch: "b".into()
                })
                .err(),
            Some(Error::Scope)
        );
        assert_eq!(
            lineage
                .binding(&Scope {
                    story: "story".into(),
                    branch: "missing".into()
                })
                .err(),
            Some(Error::Scope)
        );
    }
}
