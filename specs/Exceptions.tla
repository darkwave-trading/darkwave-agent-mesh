----------------------------- MODULE Exceptions -----------------------------
(***************************************************************************)
(* One Approval in the Agent Runtime's exceptions queue, and the handling  *)
(* waiting on it. Answers (approve, refuse, expire) race; each is a claim  *)
(* in the record keyed by the exception id alone, so exactly one wins.     *)
(* `ExceptionRepo` then follows the winner by a compare-and-set from Open; *)
(* a caller may crash between the two, so the stores can diverge, and the  *)
(* timer repairs `ExceptionRepo` from the record. `RecoverMessages`        *)
(* resumes the handling from the record, never from `ExceptionRepo`.       *)
(***************************************************************************)
EXTENDS Naturals, FiniteSets

CONSTANTS Callers,       \* operator callers that may answer at once, e.g. {c1, c2}
          Expiry,        \* the tick at which the Approval expires ("Expires at")
          MaxTime,       \* bound on the clock, to keep the model finite
          MaxCrashes     \* bound on crashes

Answers == {"approved", "refused", "expired"}
Actors == Callers \cup {"timer"}

VARIABLES
  now,                   \* the Clock, in ticks
  rec,                   \* the record's answer entry: "none" or the winning answer
  recAt,                 \* history: the tick at which the winning answer was claimed
  repo,                  \* ExceptionRepo's status: "open" or an answer
  pc,                    \* per actor: "idle" | "claim" | "follow" | "done"
  want,                  \* per actor: the answer it is giving
  reply,                 \* per actor: "none" | "won" | "same" | "refused" | "late"
  resumed,               \* what RecoverMessages resumed the handling as: "none" or an answer
  crashes

vars == <<now, rec, recAt, repo, pc, want, reply, resumed, crashes>>

TypeOK ==
  /\ now \in 0..MaxTime
  /\ rec \in {"none"} \cup Answers /\ recAt \in 0..MaxTime
  /\ repo \in {"open"} \cup Answers
  /\ pc \in [Actors -> {"idle", "claim", "follow", "done"}]
  /\ want \in [Actors -> {"none"} \cup Answers]
  /\ reply \in [Actors -> {"none", "won", "same", "refused", "late"}]
  /\ resumed \in {"none"} \cup Answers
  /\ crashes \in Nat

Init ==
  /\ now = 0 /\ rec = "none" /\ recAt = 0 /\ repo = "open"
  /\ pc = [a \in Actors |-> "idle"] /\ want = [a \in Actors |-> "none"]
  /\ reply = [a \in Actors |-> "none"] /\ resumed = "none" /\ crashes = 0

(* ----- answering: ApproveAction, RefuseAction, ExpireException ----- *)

\* The operator calls ApproveAction or RefuseAction; the timer calls ExpireException.
Call(a) ==
  /\ pc[a] = "idle" /\ reply[a] = "none"
  /\ \E w \in (IF a = "timer" THEN {"expired"} ELSE {"approved", "refused"}) :
        want' = [want EXCEPT ![a] = w]
  /\ pc' = [pc EXCEPT ![a] = "claim"]
  /\ UNCHANGED <<now, rec, recAt, repo, reply, resumed, crashes>>

\* The claim in the record, keyed by the exception id alone. The record store reads the
\* Clock inside the claim, in one step: an operator's answer when it reads at or past
\* "Expires at" is refused, and expiry is accepted only then. A reading taken by the caller
\* before the claim would open a window (Use Cases: The Message Path, S3 step 4).
Claim(a) ==
  /\ pc[a] = "claim"
  /\ IF a # "timer" /\ now >= Expiry /\ rec = "none" THEN
        /\ reply' = [reply EXCEPT ![a] = "late"] /\ pc' = [pc EXCEPT ![a] = "done"]
        /\ UNCHANGED <<rec, recAt, want>>
     ELSE IF a = "timer" /\ now < Expiry THEN               \* not yet due: nothing
        /\ pc' = [pc EXCEPT ![a] = "idle"] /\ want' = [want EXCEPT ![a] = "none"]
        /\ UNCHANGED <<rec, recAt, reply>>
     ELSE IF rec = "none" THEN                               \* this answer wins
        /\ rec' = want[a] /\ recAt' = now
        /\ reply' = [reply EXCEPT ![a] = "won"] /\ pc' = [pc EXCEPT ![a] = "follow"]
        /\ UNCHANGED want
     ELSE IF rec = want[a] THEN                              \* the same answer again: the first result
        /\ reply' = [reply EXCEPT ![a] = "same"] /\ pc' = [pc EXCEPT ![a] = "done"]
        /\ UNCHANGED <<rec, recAt, want>>
     ELSE                                                    \* a different answer: refused
        /\ reply' = [reply EXCEPT ![a] = "refused"] /\ pc' = [pc EXCEPT ![a] = "done"]
        /\ UNCHANGED <<rec, recAt, want>>
  /\ UNCHANGED <<now, repo, resumed, crashes>>

\* ExceptionRepo follows the winner: a compare-and-set from Open.
Follow(a) ==
  /\ pc[a] = "follow"
  /\ repo' = (IF repo = "open" THEN rec ELSE repo)
  /\ pc' = [pc EXCEPT ![a] = "done"]
  /\ UNCHANGED <<now, rec, recAt, want, reply, resumed, crashes>>

\* A caller dies after its claim and before ExceptionRepo follows: the stores diverge.
Crash(a) ==
  /\ pc[a] = "follow" /\ crashes < MaxCrashes
  /\ pc' = [pc EXCEPT ![a] = "done"] /\ crashes' = crashes + 1
  /\ UNCHANGED <<now, rec, recAt, repo, want, reply, resumed>>

(* ----- the timer and recovery ----- *)

Tick ==
  /\ now < MaxTime /\ now' = now + 1
  /\ UNCHANGED <<rec, recAt, repo, pc, want, reply, resumed, crashes>>

\* The record wins: the timer sets ExceptionRepo to the record's answer.
Repair ==
  /\ rec # "none" /\ repo # rec
  /\ repo' = rec
  /\ UNCHANGED <<now, rec, recAt, pc, want, reply, resumed, crashes>>

\* RecoverMessages resumes an answered handling, reading the record only.
Resume ==
  /\ rec # "none" /\ resumed = "none"
  /\ resumed' = rec
  /\ UNCHANGED <<now, rec, recAt, repo, pc, want, reply, crashes>>

Next == \/ \E a \in Actors : Call(a) \/ Claim(a) \/ Follow(a) \/ Crash(a)
        \/ Tick \/ Repair \/ Resume

Fairness ==
  /\ WF_vars(Tick) /\ WF_vars(Repair) /\ WF_vars(Resume)
  /\ WF_vars(Call("timer")) /\ WF_vars(Claim("timer"))
  /\ \A a \in Actors : WF_vars(Claim(a)) /\ WF_vars(Follow(a))

Spec == Init /\ [][Next]_vars /\ Fairness

(* ----- properties ----- *)

\* Exactly one answer wins, and it never changes.
\* Lineage: EX-01
OneWinner == Cardinality({a \in Actors : reply[a] = "won"}) <= 1
\* Lineage: EX-01
AnswerStands == [][rec # "none" => rec' = rec]_vars

\* ExceptionRepo is never ahead of, or against, the record.
\* Lineage: EX-03
RepoFollowsRecord == repo # "open" => repo = rec

\* An Approval is never approved late, and never expires early.
\* Lineage: EX-02
NeverApprovedLate == rec = "approved" => recAt < Expiry
\* Lineage: EX-02
NeverExpiredEarly == rec = "expired" => recAt >= Expiry

\* A caller told "won" or "same" holds the answer that stands.
\* Lineage: EX-05
RepliesTrue == \A a \in Callers : reply[a] \in {"won", "same"} => want[a] = rec

\* The handling is resumed as the record says, never as ExceptionRepo says.
\* Lineage: EX-04
ResumedByRecord == resumed # "none" => resumed = rec

\* In the end the Approval is answered, the stores agree and the handling resumes.
\* Lineage: EX-03
Settles == <>[](rec # "none" /\ repo = rec /\ resumed = rec)

\* Reachability checks: each must be violated.
NotDiverged == ~(rec # "none" /\ repo = "open" /\ \A a \in Actors : pc[a] # "follow")
NotLateRefused == \A a \in Callers : reply[a] # "late"
NotRaceRefused == \A a \in Callers : reply[a] # "refused"
=============================================================================
