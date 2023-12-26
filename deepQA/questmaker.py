import time
from deepllm.interactors import Agent
from deepllm.api import *


def localize(local):
    if local:
        local_model()
    else:
        key = os.getenv("OPENAI_API_KEY")
        set_openai_api_key(key)
        # smarter_model()
        cheaper_model()


def make_agent():
    agent = Agent(name='QA_generator')
    agent.resume()

    return agent

class SymTable:
    def __init__(self):
        self.syms = dict()
        self.nums = []

    def add(self, sym):
        n = self.syms.get(sym)
        if n is None:
            n = len(self.nums)
            self.syms[sym] = len(self.nums)
            self.nums.append(sym)
        return n

    def __contains__(self, sym):
        return sym in self.syms

    def __len__(self):
        return len(self.nums)

    def __repr__(self):
        return str(self.syms)


def clean_sent(sent):
    sent = sent.strip().replace(' .', '.').replace('..', '')
    sent = sent.replace(' -', '-').replace("'", "_")
    sent = " ".join(sent.split())
    if not sent.endswith('.'): sent = sent + "."
    return sent


def clean_quest(x0, sent, context):
    x = x0.strip()
    # print('!!! CLEANING:', x)

    assert x, ("Empty!!!!", (sent, context))

    assert 'A:' in x or 'Q:' in x, ('MISSING A: or Q:', x)

    if x[0] in ("'", '"'): x = x[1:]
    if x[-1] in ("'", '"'): x = x[0:-1]

    assert x and x[0:3] in ['Q: ', 'A: '], x0
    return x


def to_quests(agent, question, context, k=3):
    agent.set_pattern(None)
    p = f"""
    With the context "{context}" in mind,
    generate {k} different answers to "{question}".
    Prefix each answer with "A:", but do NOT number them as in "A1: or 1. ".
    After returning each answer, suggest a salient follow-up question to your answer, prefixed with "Q:" . 
    """
    prompt = " ".join(p.split())

    answer = agent.ask(prompt)

    # print('PROMPT:',prompt)
    # print('!!! RETURN:\n',answer)
    # print()

    return answer


def quest2quests(agent, quest, context, k=3):
    t1 = time.time()

    quests_ = to_quests(agent, quest, context, k=k)
    quests0 = quests_.replace('\n\n', '\n').split('\n')

    quests = [clean_quest(q, quest, context) for q in quests0]
    # print('LENS:', len(quests0), len(quests))
    if len(quests) % 2 != 0:
        quests = quests[0:-1]  # fix LLM ignoring instruction
    # assert len(quests) % 2 == 0, (len(quests0), len(quests), quest, quests0)

    pairs = []
    for j, x in enumerate(quests):

        p = x[0:3]
        assert p in ['Q: ', 'A: ']
        x = x[3:]
        if j % 2 == 0:
            assert p == "A: ", (p, x)
            a = x  # answers

            q = quests[j + 1]
            p_ = q[0:3]
            q = q[3:]  # quest: next position
            assert p_ == "Q: ", (p_, q)
            pair = (a, q)
            pairs.append(pair)

    t2 = time.time()
    #print('TIME:', round(t2 - t1, 4))
    #print('COSTS:', round(agent.dollar_cost(), 4))
    return pairs


def one_quest(agent, quest, context, trim_size=3):
    agent.set_initiator(quest)
    res = quest2quests(agent, quest, context, k=1)
    agent.trim_at(trim_size)
    agent.persist()
    a, q = res[0]
    return a, q


def test_questmaker():
    print('TESTING:')
    localize(0)
    agent = make_agent()
    qs=quest2quests(agent, "What is a neural network?", "", k=3)
    print(qs)


if __name__ == "__main__":
    test_questmaker()