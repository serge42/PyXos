from enum import Enum, unique


@unique
class Indicators(Enum):
    CLIENTS = 'cli'
    ACCEPTORS = 'acc'
    PROPOSERS = 'prp'
    LEARNERS_REQ = 'lrn'
    LEARNERS_REP = 'lrp'
    PHASE1A = 'p1a'
    PHASE1B = 'p1b'
    PHASE2A = 'p2a'
    PHASE2B = 'p2b'


class Message:
    def __init__(self, indicator, msg):
        self.indicator = indicator
        self.msg = msg


class Phase1a:
    def __init__(self, id, b):
        self.proposer = id
        self.ballot_num = b


class Phase1b:
    def __init__(self, b, aid, accepted):
        self.ballot_num = b
        self.acceptor_id = aid
        self.accepted = accepted

    def to_string(self):
        return str.format("<PHASE1B: val={0}, acceptor={1}, ballot={2}, accepted={3}",
                          self.acceptor_id, self.ballot_num, self.accepted)


class Phase2a:
    def __init__(self, b, value):
        self.ballot_num = b
        self.value = value


class Phase2b:
    def __init__(self, b, aid, value):
        self.ballot_num = b
        self.acceptor_id = aid
        self.value = value

class Result:
    def __init__(self, b, value):
        self.ballot_num = b
        self.value = value
