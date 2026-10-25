---------------------------- MODULE MessagePath ----------------------------
(***************************************************************************)
(* One handling of one message by one Agent, in the Agent Runtime.         *)
(* Several handlers may run it at once (a redelivery, a second process,    *)
(* recovery); any handler may crash between any two writes; the gateway    *)
(* may succeed, fail, or give no answer; the operator answers exceptions.  *)
(* Every record entry is a claim: written only if absent.                  *)
(***************************************************************************)
EXTENDS Naturals

CONSTANTS Handlers,      \* handler identities, e.g. {p1, p2}
          MaxAttempts,   \* the Agent's attempt limit
          MaxCrashes,    \* bound on crashes, to keep the model finite
          Person,        \* TRUE: the Agent's proposer is a person
          Budget,        \* TRUE: the Agent's budget may be reached before the proposer is asked
          Dup            \* TRUE: the same id may arrive again with a different digest

\* "advisory" stands for both its causes (a failed action; a proposer timeout or refusal); they exclude each other in one handling.
Kinds == {"approval", "unknown", "advisory", "limit", "ask", "budget"}
Stopping == {"approval", "unknown", "limit", "ask"}   \* kinds the handling waits on
\* The budget Problem is Stopping for the Agent, not for this handling: it is about the Agent
\* and the period, and the handling it stops is refused and closed, not left waiting.

VARIABLES
  received, checked,     \* entries
  proposal,              \* "none" | "asked" | "given"
  provFail,              \* the proposer timed out or refused
  inputBad,              \* the input check failed
  decision,              \* "none" | "allow" | "hold" | "refuse"
  redecision,            \* "none" | "allow" | "refuse"   (after an approval)
  intent,                \* the intent claim
  outcome,               \* "none" | "succ" | "fail" | "stated"
  closed,                \* the closing entry
  budgetOut,             \* refused: the Agent's budget is reached
  digest,                \* "none" | the digest on the received entry
  attempts,              \* attempt entries written
  exc,                   \* [Kinds -> status]
  raised,                \* [Kinds -> times raised], to check "at most once"
  pc, won, result,       \* handler-local state
  dig,                   \* handler-local: the digest of the bytes this handler was given
  dupRefused,            \* a duplicate refused, keyed apart from the handling
  crashes, done,         \* environment: crashes so far; times the action took effect
  actDig                 \* history: the digest of the message whose action was claimed

entries == <<received, checked, proposal, provFail, inputBad, decision,
             redecision, intent, outcome, closed, attempts, budgetOut, digest>>
vars == <<entries, exc, raised, pc, won, result, crashes, done, dig, dupRefused, actDig>>

ExcStatus == {"none", "open", "approved", "refused", "expired", "resolved"}

TypeOK ==
  /\ received \in BOOLEAN /\ checked \in BOOLEAN
  /\ proposal \in {"none", "asked", "given"}
  /\ provFail \in BOOLEAN /\ inputBad \in BOOLEAN
  /\ decision \in {"none", "allow", "hold", "refuse"}
  /\ redecision \in {"none", "allow", "refuse"}
  /\ intent \in BOOLEAN
  /\ outcome \in {"none", "succ", "fail", "stated"}
  /\ closed \in BOOLEAN
  /\ attempts \in Nat
  /\ exc \in [Kinds -> ExcStatus]
  /\ raised \in [Kinds -> Nat]
  /\ pc \in [Handlers -> {"idle", "begin", "run", "perform", "settle"}]
  /\ won \in [Handlers -> BOOLEAN]
  /\ result \in [Handlers -> {"none", "succ", "fail", "silent"}]
  /\ budgetOut \in BOOLEAN /\ digest \in {"none", "a", "b"}
  /\ dig \in [Handlers -> {"a", "b"}] /\ dupRefused \in BOOLEAN /\ actDig \in {"none", "a", "b"}

(* ----- derived states ----- *)
Waiting == \E k \in Stopping : exc[k] = "open"   \* "acknowledged" counts as waiting too; it is not modelled

\* A live intent lease: a handler holds the claim and has not yet settled.
InFlight == \E q \in Handlers : won[q]

Refusal ==
  \/ inputBad \/ provFail \/ budgetOut
  \/ decision = "refuse" \/ redecision = "refuse"
  \/ exc["approval"] \in {"refused", "expired"}
  \/ exc["ask"] = "expired"

MayAct == decision = "allow" \/ (exc["approval"] = "approved" /\ redecision = "allow")

Owed == \* the exception the handling owes before it may close, if any
  IF (outcome = "fail" \/ provFail) /\ raised["advisory"] = 0 THEN "advisory"
  ELSE IF budgetOut /\ raised["budget"] = 0 THEN "budget"
  ELSE "none"

Raise(k) == \* create-if-absent over all time: one exception of each kind per handling
  /\ raised[k] = 0
  /\ exc' = [exc EXCEPT ![k] = "open"]
  /\ raised' = [raised EXCEPT ![k] = @ + 1]   \* counts, so EachKindOnce can fail

Init ==
  /\ received = FALSE /\ checked = FALSE /\ proposal = "none"
  /\ provFail = FALSE /\ inputBad = FALSE
  /\ decision = "none" /\ redecision = "none"
  /\ intent = FALSE /\ outcome = "none" /\ closed = FALSE /\ attempts = 0
  /\ exc = [k \in Kinds |-> "none"] /\ raised = [k \in Kinds |-> 0]
  /\ pc = [p \in Handlers |-> "idle"] /\ won = [p \in Handlers |-> FALSE]
  /\ result = [p \in Handlers |-> "none"]
  /\ crashes = 0 /\ done = 0
  /\ budgetOut = FALSE /\ digest = "none"
  /\ dig = [p \in Handlers |-> "a"] /\ dupRefused = FALSE /\ actDig = "none"

Go(p, s) == pc' = [pc EXCEPT ![p] = s]

(* ----- a handler ----- *)

\* A delivery, a redelivery or recovery starts a run.
Start(p) ==
  /\ pc[p] = "idle" /\ ~closed
  /\ Go(p, "begin")
  /\ dig' \in [Handlers -> {"a", "b"}] /\ \A q \in Handlers \ {p} : dig'[q] = dig[q]
  \* "a" names whichever copy is received first; "b", one later copy with another digest
  /\ (dig'[p] = "a" \/ (Dup /\ received /\ ~dupRefused))
  /\ UNCHANGED <<entries, exc, raised, won, result, crashes, done, dupRefused, actDig>>

\* Step 1, in order: the received entry; stop if closed, waiting or leased;
\* an intent with no outcome raises "outcome unknown"; a resolved attempt-limit
\* Problem closes; a recorded outcome or refusal goes on to close; the attempt entry; the limit.
Begin(p) ==
  /\ pc[p] = "begin"
  /\ ~received \/ dig[p] = digest                   \* a different digest is RefuseDuplicate's
  /\ IF ~received THEN
        /\ received' = TRUE /\ digest' = dig[p]
        /\ UNCHANGED <<budgetOut, checked, proposal, provFail, inputBad, decision, redecision,
                       intent, outcome, closed, attempts, exc, raised, pc>>
     ELSE IF closed \/ Waiting \/ InFlight THEN
        /\ Go(p, "idle")
        /\ UNCHANGED <<entries, exc, raised>>
     ELSE IF intent /\ outcome = "none" THEN         \* the lease has run out: outcome unknown
        /\ Raise("unknown") /\ UNCHANGED <<entries, pc>>
     ELSE IF exc["limit"] = "resolved" THEN      \* ended by the operator; nothing can be owed here,
                                                 \* since the limit is raised only when nothing owing is recorded
        /\ closed' = TRUE /\ Go(p, "idle")
        /\ UNCHANGED <<received, checked, proposal, provFail, inputBad, decision,
                       redecision, intent, outcome, attempts, exc, raised, budgetOut, digest>>
     ELSE IF outcome # "none" \/ Refusal THEN       \* an outcome or a refusal is recorded: no attempt, no limit
        /\ Go(p, "run") /\ UNCHANGED <<entries, exc, raised>>
     ELSE IF attempts >= MaxAttempts THEN
        /\ Raise("limit") /\ Go(p, "idle")
        /\ UNCHANGED entries
     ELSE
        /\ attempts' = attempts + 1 /\ Go(p, "run")
        /\ UNCHANGED <<received, checked, proposal, provFail, inputBad, decision,
                       redecision, intent, outcome, closed, exc, raised, budgetOut, digest>>
  /\ UNCHANGED <<won, result, crashes, done, dig, dupRefused, actDig>>

\* Step 1a: the same id with a different digest is refused, keyed apart; nothing is
\* written to the original handling.
RefuseDuplicate(p) ==
  /\ pc[p] = "begin" /\ received /\ dig[p] # digest
  /\ dupRefused' = TRUE /\ Go(p, "idle")
  /\ UNCHANGED <<entries, exc, raised, won, result, crashes, done, dig, actDig>>

\* Steps 2 to 6: one write per step, chosen from what the record shows.
Keep == UNCHANGED <<received, checked, proposal, provFail, inputBad, decision,
                    redecision, intent, outcome, closed, attempts, budgetOut, digest>>

Run(p) ==
  /\ pc[p] = "run"
  /\ \/ /\ (closed \/ Waiting \/ exc["limit"] = "resolved")  \* nothing to do now; an ended handling is closed by Begin
        /\ Go(p, "idle") /\ Keep /\ UNCHANGED <<exc, raised>>
     \/ /\ ~closed /\ ~Waiting /\ exc["limit"] # "resolved"
        /\ CASE
             \* a refusal of any kind: owe, then close
             Refusal /\ Owed # "none" ->
                Raise(Owed) /\ Keep /\ UNCHANGED pc
          [] Refusal ->
                closed' = TRUE /\ Go(p, "idle")
                /\ UNCHANGED <<received, checked, proposal, provFail, inputBad, decision,
                               redecision, intent, outcome, attempts, exc, raised, budgetOut, digest>>
             \* an outcome: owe, then close
          [] outcome # "none" /\ Owed # "none" ->
                Raise(Owed) /\ Keep /\ UNCHANGED pc
          [] outcome # "none" ->
                closed' = TRUE /\ Go(p, "idle")
                /\ UNCHANGED <<received, checked, proposal, provFail, inputBad, decision,
                               redecision, intent, outcome, attempts, exc, raised, budgetOut, digest>>
             \* step 2: check the input
          [] ~checked ->
                \/ checked' = TRUE /\ UNCHANGED inputBad
                \/ inputBad' = TRUE /\ UNCHANGED checked
                /\ UNCHANGED <<received, proposal, provFail, decision, redecision,
                               intent, outcome, closed, attempts, exc, raised, pc, budgetOut, digest>>
             \* step 3: propose
          [] proposal = "none" /\ Person ->
                \/ Budget /\ budgetOut' = TRUE /\ UNCHANGED proposal   \* step 3: the budget is checked first
                \/ proposal' = "asked" /\ UNCHANGED budgetOut
                /\ UNCHANGED <<received, checked, provFail, inputBad, decision, redecision,
                               intent, outcome, closed, attempts, exc, raised, pc, digest>>
          [] proposal = "none" ->
                \/ Budget /\ budgetOut' = TRUE /\ UNCHANGED <<proposal, provFail>>
                \/ proposal' = "given" /\ UNCHANGED <<provFail, budgetOut>>
                \/ provFail' = TRUE /\ UNCHANGED <<proposal, budgetOut>>
                /\ UNCHANGED <<received, checked, inputBad, decision, redecision,
                               intent, outcome, closed, attempts, exc, raised, pc, digest>>
          [] proposal = "asked" /\ raised["ask"] = 0 ->
                Raise("ask") /\ Keep /\ UNCHANGED pc
             \* step 4: decide
          [] proposal = "given" /\ decision = "none" ->
                \E d \in IF Person THEN {"allow", "refuse"} ELSE {"allow", "hold", "refuse"} :
                   decision' = d
                /\ UNCHANGED <<received, checked, proposal, provFail, inputBad, redecision,
                               intent, outcome, closed, attempts, exc, raised, pc, budgetOut, digest>>
          [] decision = "hold" /\ raised["approval"] = 0 ->
                Raise("approval") /\ Keep /\ UNCHANGED pc
          [] decision = "hold" /\ exc["approval"] = "approved" /\ redecision = "none" ->
                \E d \in {"allow", "refuse"} : redecision' = d   \* a hold stands as approved
                /\ UNCHANGED <<received, checked, proposal, provFail, inputBad, decision,
                               intent, outcome, closed, attempts, exc, raised, pc, budgetOut, digest>>
             \* step 5: the intent claim
          [] MayAct /\ ~intent -> FALSE              \* Claim(p) takes this step
          \* the intent's lease has run out: its holder is gone (the lease outlasts
          \* the gateway's own timeout, so a live holder always settles first)
          [] MayAct /\ intent /\ \A q \in Handlers : ~won[q] ->
                Raise("unknown") /\ Keep /\ Go(p, "idle")
          [] MayAct /\ intent ->                     \* another handler holds the lease
                Go(p, "idle") /\ Keep /\ UNCHANGED <<exc, raised>>
          [] OTHER ->
                Go(p, "idle") /\ Keep /\ UNCHANGED <<exc, raised>>
  /\ UNCHANGED <<won, result, crashes, done, dig, dupRefused, actDig>>

\* Step 5: the intent claim. Exactly one handler wins it.
Claim(p) ==
  /\ pc[p] = "run" /\ ~closed /\ ~Waiting /\ ~Refusal /\ outcome = "none"
  /\ exc["limit"] # "resolved"                     \* the operator ended the handling
  /\ MayAct /\ ~intent
  /\ intent' = TRUE /\ won' = [won EXCEPT ![p] = TRUE] /\ Go(p, "perform")
  /\ actDig' = dig[p] /\ UNCHANGED <<dig, dupRefused>>
  /\ UNCHANGED <<received, checked, proposal, provFail, inputBad, decision,
                 redecision, outcome, closed, attempts, exc, raised, result, crashes, done, budgetOut, digest>>

\* The gateway: succeeds, fails (certainly not done), or gives no answer.
Perform(p) ==
  /\ pc[p] = "perform"
  /\ \/ done' = done + 1 /\ result' = [result EXCEPT ![p] = "succ"]
     \/ UNCHANGED done   /\ result' = [result EXCEPT ![p] = "fail"]
     \/ done' = done + 1 /\ result' = [result EXCEPT ![p] = "silent"]
     \/ UNCHANGED done   /\ result' = [result EXCEPT ![p] = "silent"]
  /\ Go(p, "settle")
  /\ UNCHANGED <<entries, exc, raised, won, crashes, dig, dupRefused, actDig>>

\* Write the outcome, a claim; no answer writes nothing and raises "unknown".
Settle(p) ==
  /\ pc[p] = "settle"
  /\ IF result[p] \in {"succ", "fail"} /\ outcome = "none"
       THEN outcome' = result[p] /\ UNCHANGED <<exc, raised>>
     ELSE IF result[p] = "silent" /\ outcome = "none"
       THEN Raise("unknown") /\ UNCHANGED outcome
     ELSE UNCHANGED <<outcome, exc, raised>>
  /\ won' = [won EXCEPT ![p] = FALSE] /\ result' = [result EXCEPT ![p] = "none"]
  /\ Go(p, "idle")
  /\ UNCHANGED <<received, checked, proposal, provFail, inputBad, decision,
                 redecision, intent, closed, attempts, crashes, done, dig, dupRefused, actDig, budgetOut, digest>>

\* A crash or a failed write: the handler stops; its local state is lost.
Crash(p) ==
  /\ pc[p] # "idle" /\ crashes < MaxCrashes
  /\ crashes' = crashes + 1
  /\ Go(p, "idle")
  /\ won' = [won EXCEPT ![p] = FALSE] /\ result' = [result EXCEPT ![p] = "none"]
  /\ UNCHANGED <<entries, exc, raised, done, dig, dupRefused, actDig>>

(* ----- the operator and time ----- *)
OpKeep == UNCHANGED <<pc, won, result, crashes, done, raised, dig, dupRefused, actDig>>

Approve == exc["approval"] = "open" /\ exc' = [exc EXCEPT !["approval"] = "approved"]
           /\ UNCHANGED entries /\ OpKeep
RefuseA == exc["approval"] = "open" /\ exc' = [exc EXCEPT !["approval"] = "refused"]
           /\ UNCHANGED entries /\ OpKeep
ExpireA == exc["approval"] = "open" /\ exc' = [exc EXCEPT !["approval"] = "expired"]
           /\ UNCHANGED entries /\ OpKeep

\* ProposeAction: the person's proposal, a claim; the "ask" exception closes.
ProposeAction == exc["ask"] = "open" /\ proposal = "asked"
           /\ proposal' = "given" /\ exc' = [exc EXCEPT !["ask"] = "resolved"]
           /\ UNCHANGED <<received, checked, provFail, inputBad, decision, redecision,
                          intent, outcome, closed, attempts, budgetOut, digest>> /\ OpKeep
ExpireAsk == exc["ask"] = "open" /\ exc' = [exc EXCEPT !["ask"] = "expired"]
           /\ UNCHANGED entries /\ OpKeep

\* ResolveProblem for "outcome unknown": his statement is the only outcome, if none was written.
ResolveUnknown == exc["unknown"] = "open"
           /\ outcome' = (IF outcome = "none" THEN "stated" ELSE outcome)
           /\ exc' = [exc EXCEPT !["unknown"] = "resolved"]
           /\ UNCHANGED <<received, checked, proposal, provFail, inputBad, decision,
                          redecision, intent, closed, attempts, budgetOut, digest>> /\ OpKeep

\* ResolveProblem or RetryAfterProblem for the attempt limit: the handling is ended.
ResolveLimit == exc["limit"] = "open" /\ exc' = [exc EXCEPT !["limit"] = "resolved"]
           /\ UNCHANGED entries /\ OpKeep

Handler(p) == Start(p) \/ Begin(p) \/ RefuseDuplicate(p) \/ Run(p) \/ Claim(p) \/ Perform(p) \/ Settle(p) \/ Crash(p)
Operator == Approve \/ RefuseA \/ ExpireA \/ ProposeAction \/ ExpireAsk
            \/ ResolveUnknown \/ ResolveLimit

Next == (\E p \in Handlers : Handler(p)) \/ Operator

Fairness ==
  /\ \A p \in Handlers : WF_vars(Start(p)) /\ WF_vars(Begin(p)) /\ WF_vars(RefuseDuplicate(p)) /\ WF_vars(Run(p)) /\ WF_vars(Claim(p))
                         /\ WF_vars(Perform(p)) /\ WF_vars(Settle(p))
  /\ WF_vars(ExpireA) /\ WF_vars(ExpireAsk)              \* time passes
  /\ WF_vars(ResolveUnknown) /\ WF_vars(ResolveLimit)    \* the operator answers in the end

Spec == Init /\ [][Next]_vars /\ Fairness

(* ----- properties ----- *)
\* Lineage: INV-04
AtMostOnce == done <= 1

\* Lineage: INV-01, MP-04
NoActionWithoutAllow ==
  done > 0 => (intent /\ (decision = "allow"
                          \/ (exc["approval"] = "approved" /\ redecision = "allow")))

\* Lineage: EX-07
EachKindOnce == \A k \in Kinds : raised[k] <= 1

\* Lineage: INV-03, MP-06, MP-07
OwedBeforeClose ==
  closed => /\ ((outcome = "fail" \/ provFail) => raised["advisory"] = 1)
            /\ (budgetOut => raised["budget"] = 1)

\* The budget is checked before the proposer is asked: a refusal for the budget proposes nothing.
\* Lineage: MP-07
BudgetBeforeProposal == budgetOut => (proposal = "none" /\ ~intent /\ done = 0)

\* Only the message as first received is acted on: a duplicate with another digest never is.
\* Lineage: MP-03
DupNeverActs == done > 0 => actDig = digest

\* Lineage: INV-04, MP-01
IntentSettled == closed /\ intent => outcome # "none"   \* an action begun is never closed unsettled

\* Once the attempt limit is raised, no action is begun or done: the operator's end stands.
\* Lineage: MP-02, MP-01, INV-04
LimitEndsAction == raised["limit"] = 1 => (~intent /\ done = 0)

\* The record never lies about the world: "succeeded" means done, "failed" means certainly not done.
\* Lineage: MP-06
OutcomeTrue == (outcome = "succ" => done = 1) /\ (outcome = "fail" => done = 0)

\* "Outcome unknown" is settled only by the operator's statement.
\* Lineage: EX-06
UnknownOnlyStated == (raised["unknown"] = 1 /\ outcome # "none") => outcome = "stated"

\* Lineage: INV-04, MP-01
UnknownNeverRun == \* once "unknown" is raised, no handler performs
  exc["unknown"] # "none" => \A p \in Handlers : pc[p] # "perform"

\* An action property: nothing is written after the closing entry.
\* Lineage: INV-03
NothingAfterClose == [][closed => UNCHANGED entries]_vars

\* Every handling ends.
\* Lineage: INV-03, INV-10
EventuallyClosed == <>closed
\* Reachability checks: each must be violated, showing the path is not vacuous.
NotActedAndClosed == ~(done = 1 /\ closed /\ outcome = "succ")
NotApprovedActed == ~(done = 1 /\ redecision = "allow" /\ closed)
NotStatedClosed == ~(outcome = "stated" /\ closed)
NotEndedByOperator == ~(exc["limit"] = "resolved" /\ closed)
NotBudgetRefused == ~(budgetOut /\ closed)
NotDupRefused == ~(dupRefused /\ done = 1)
\* Person configuration: a person's proposal acted on; a Proposal asked expiring.
NotPersonActed == ~(proposal = "given" /\ exc["ask"] = "resolved" /\ done = 1 /\ closed)
NotAskExpiredClosed == ~(exc["ask"] = "expired" /\ closed)
=============================================================================
