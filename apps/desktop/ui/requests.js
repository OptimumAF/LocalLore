export const envelope = command => ({ version: 1, command });
export function actionRequest(scope, turn, revision, kind) {
  return { version: 1, scope, turn, expected_revision: revision, intent: { kind: 'actions', value: [kind === 'ability'
    ? { op: 'use_ability', ability: 'teleport' }
    : { op: 'give', item: 'potion', to: 'mira', quantity: 1 }] } };
}
