## PyXos
Paxos implementation by Sébastien Bouquet

### Building/environment

This implementation was done using Python 3.7
The packages used are:

- enum
- pickle
- select
- socket
- sys
- time

No building required, the provided launching scripts call the "python3" command which is an alias to the CPython interpreter.

### Known limitations

 1. he leader election is not implemented: if the current leader fails another proposer won't be elected.
 2. total order may be violated