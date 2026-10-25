# Specifications

Two [TLA+](https://lamport.azurewebsites.net/tla/tla.html) specifications of the Agent Runtime, checked with the TLC model checker. They describe the design; there is no implementation yet.

| File | What it specifies |
|---|---|
| `MessagePath.tla` | One handling of one message by one Agent: several handlers at once, a crash between any two writes, a gateway that may succeed, fail or not answer. |
| `Exceptions.tla` | One Approval in the exceptions queue: answers (approve, refuse, expire) racing, so exactly one wins, and recovery from the record. |

Each `.cfg` file is one model configuration: its constants, the invariants and the temporal properties TLC checks. The `-large` and `-person` variants widen the model or switch the proposer to a person.

## Run

Needs Java and `tla2tools.jar` from the [TLA+ releases](https://github.com/tlaplus/tlaplus/releases). From the directory that holds `specs/`:

```sh
java -cp tla2tools.jar tlc2.TLC -workers auto -config specs/MessagePath.cfg specs/MessagePath.tla
java -cp tla2tools.jar tlc2.TLC -workers auto -config specs/MessagePath-person.cfg specs/MessagePath.tla
java -cp tla2tools.jar tlc2.TLC -workers auto -config specs/Exceptions.cfg specs/Exceptions.tla
```

`check-reach.sh tla2tools.jar` confirms that the paths the invariants guard are reachable in the model, so no property passes only because the model never gets there. It expects each of its checks to be violated.

Each invariant is named for the guarantee it checks. A model checker covers the bounded configurations in the `.cfg` files, not every size.
