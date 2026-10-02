from collections import defaultdict

def calculate_balances(expenses, settlements):
    balances = defaultdict(float)

    for expense in expenses:
        shared_participants = [
            share.participant_id
            for share in expense.shares
        ]

        if not shared_participants:
            continue

        split_amount = expense.amount / len(shared_participants)
        balances[expense.paid_by_id] += expense.amount

        for participant_id in shared_participants:
            balances[participant_id] -= split_amount
    
    for settlement in settlements:
        balances[settlement.payer_id] -= settlement.amount
        balances[settlement.receiver_id] += settlement.amount
    return balances