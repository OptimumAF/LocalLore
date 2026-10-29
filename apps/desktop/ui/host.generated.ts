/* Generated from Rust host-v1.schema.json. Do not edit. */

export type HostCommand =
    | {
          op: "capabilities";
      }
    | {
          op: "workspace";
      }
    | {
          op: "branches";
          story: string;
      }
    | {
          op: "resume";
          scope: Scope;
      }
    | {
          op: "create";
          seed: string;
      }
    | {
          op: "story_templates";
      }
    | {
          op: "story_template";
          template: string;
      }
    | {
          op: "story_setup";
          player_name?: string | null;
          template: string;
      }
    | {
          op: "story_presentation";
          player_name?: string | null;
          presentation?: StoryPresentationV1 | null;
          template: string;
      }
    | {
          expected_revision: number;
          op: "story_presentation_view";
          scope: Scope;
          session: string;
      }
    | {
          creation_id: string;
          op: "create_named";
          seed_sha256: string;
          template: string;
          title: string;
      }
    | {
          creation_id: string;
          op: "create_configured";
          player_name: string;
          setup_sha256: string;
          template: string;
          template_sha256: string;
          title: string;
      }
    | {
          creation_id: string;
          op: "create_presented";
          player_name: string;
          presentation: StoryPresentationV1;
          setup_sha256: string;
          template: string;
          template_sha256: string;
          title: string;
      }
    | {
          op: "open";
          scope: Scope;
          session: string;
      }
    | {
          op: "close";
          scope: Scope;
          session: string;
      }
    | {
          mode: Mode;
          op: "submit";
          request: Request;
          session: string;
      }
    | {
          op: "prepare";
          scope: Scope;
          session: string;
          turn: string;
      }
    | {
          op: "commit";
          scope: Scope;
          session: string;
          turn: string;
      }
    | {
          op: "cancel";
          scope: Scope;
          session: string;
          turn: string;
      }
    | {
          op: "turn_status";
          scope: Scope;
          session: string;
          turn: string;
      }
    | {
          expected_revision: number;
          observer: string;
          op: "inspect";
          scope: Scope;
          session: string;
      }
    | {
          op: "inspection_query";
          query: Query;
          session: string;
      }
    | {
          enabled: boolean;
          expected_head: number;
          op: "trace_configure";
          scope: Scope;
          session: string;
      }
    | {
          attempt?: number | null;
          base_revision: number;
          expected_head: number;
          observer: Observer;
          op: "trace_read";
          scope: Scope;
          session: string;
          turn?: string | null;
      }
    | {
          expected_head: number;
          op: "trace_clear";
          scope: Scope;
          session: string;
      }
    | {
          consent: boolean;
          enabled: boolean;
          expected_head: number;
          op: "trace_capture_configure";
          scope: Scope;
          session: string;
      }
    | {
          attempt: number;
          base_revision: number;
          expected_head: number;
          op: "trace_capture_read";
          scope: Scope;
          session: string;
          turn: string;
      }
    | {
          op: "trace_capture_revoke";
          scope: Scope;
          session: string;
      }
    | {
          op: "model_status";
      }
    | {
          expected_revision: number;
          op: "play_snapshot";
          scope: Scope;
          session: string;
      }
    | {
          expected_revision: number;
          op: "play_snapshot_v2";
          scope: Scope;
          session: string;
      }
    | {
          op: "free_text";
          request: Request;
          session: string;
      }
    | {
          expected_revision: number;
          op: "snapshot_export";
          scope: Scope;
          session: string;
      };
export type StoryTone = "plain" | "warm" | "brisk";
export type Mode =
    "accepted" | "delayed" | "malformed" | "rejected" | "failed" | "cancelled";
/**
 * This comes from explicit UI selection/clarification, never the model's interpretation alone.
 */
export type Intent =
    | {
          kind: "actions";
          value: Command[];
      }
    | {
          kind: "dialogue";
          value: {
              audience: string[];
              text: string;
          };
      }
    | {
          kind: "thought";
          value: string;
      }
    | {
          kind: "ambiguous";
          value: string;
      }
    | {
          kind: "author_correction";
          value: string;
      }
    | {
          kind: "free_text";
          value: {
              kind: PlayInputKind;
              text: string;
          };
      };
export type Command =
    | {
          item: string;
          op: "give";
          quantity: number;
          to: string;
      }
    | {
          item: string;
          op: "consume";
      }
    | {
          ability: string;
          op: "use_ability";
      }
    | {
          ability: string;
          op: "learn";
      }
    | {
          op: "move";
          to: string;
      }
    | {
          audience: string[];
          op: "say";
          text: string;
      }
    | {
          claim_event: number;
          op: "believe";
      }
    | {
          fact: string;
          op: "discover";
      }
    | {
          deadline: number;
          id: string;
          op: "promise";
          return_item?: string | null;
          terms: string;
          to: string;
      }
    | {
          id: string;
          op: "complete_promise";
      }
    | {
          op: "wait";
          ticks: number;
      };
export type PlayInputKind = "action" | "dialogue";
export type Observer =
    | {
          kind: "player";
      }
    | {
          id: string;
          kind: "character";
      }
    | {
          kind: "omniscient";
      };
export type View =
    | "profiles"
    | "history"
    | "relationships"
    | "knowledge"
    | "promises"
    | "provenance"
    | "turn_diff"
    | "summaries"
    | "retrieval_indexes";

/**
 * One source of truth for the generated frontend JSON Schema. No arbitrary seed import.
 */
export interface Envelope {
    command: HostCommand;
    version: 1;
}
export interface Scope {
    branch: string;
    story: string;
}
export interface StoryPresentationV1 {
    excluded_phrases: string[];
    tone: StoryTone;
    version: number;
}
export interface Request {
    expected_revision: number;
    intent: Intent;
    scope: Scope;
    turn: string;
    version: number;
}
export interface Query {
    at_revision?: number | null;
    cursor?: string | null;
    /**
     * Current authoritative head, even when inspecting a historical completed turn.
     */
    expected_head: number;
    limit: number;
    observer: Observer;
    scope: Scope;
    /**
     * Literal case-insensitive substring of eligible serialized rows; not SQL/FTS syntax.
     */
    search: string;
    version: number;
    view: View;
}
