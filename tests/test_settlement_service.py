from app.services.settlement_service import calculate_balances

class MockExpense:
    def __init__(self, amount, paid_by_id, shares):
        self.amount = amount
        self.paid_by_id = paid_by_id
        self.shares = shares

class MockShare:
    def __init__(self, participant_id):
        self.participant_id = participant_id

def test_equal_split_between_two_people():
    expense = MockExpense(
        amount=60,
        paid_by_id=1,
        shares=[
            MockShare(1),
            MockShare(2)
        ]
    )

    balances = calculate_balances([expense])
    assert balances[1] == 30
    assert balances[2] == -30

def test_single_participant_pays_only_for_self():
    expense = MockExpense(
        amount=40,
        paid_by_id=1,
        shares=[
            MockShare(1)
        ]
    )

    balances = calculate_balances([expense])
    assert balances[1] == 0

def test_excluded_participant_not_charged():
    expense = MockExpense(
        amount=90,
        paid_by_id=1,
        shares=[
            MockShare(1),
            MockShare(2)
        ]
    )

    balances = calculate_balances([expense])
    assert 3 not in balances