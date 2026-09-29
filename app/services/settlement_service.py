from collections import defaultdict


def calculate_balances(expenses, participants):
    balances = defaultdict(float)
    participant_count = len(participants)

    if participant_count == 0:
        return balances
    for expense in expenses:
        split_amount = expense.amount / participant_count
        balances[expense.paid_by_id] += expense.amount
        for participant in participants:
            balances[participant.id] -= split_amount
    return balances