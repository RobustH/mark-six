
import sys
import logging

# Simple mock class to test the math logic
class MockBacktester:
    def calc_next_bet(self, accumulated_loss, target_profit, odds):
        if odds <= 1: return 0
        return (accumulated_loss + target_profit) / (odds - 1)

def test_loss_recovery():
    print("Testing Loss Recovery Math...")
    
    # Case 1: Odds 1.98 (Odd/Even). Target Profit 10.
    # Round 1: Bet 10. Loss.
    loss = 10
    target = 10
    odds = 1.98
    
    # Next Bet
    next_bet = (loss + target) / (odds - 1)
    # (10 + 10) / 0.98 = 20 / 0.98 = 20.40816...
    
    expected = 20.408163265306122
    print(f"Case 1: Loss {loss}, Target {target}, Odds {odds}")
    print(f"Next Bet Needed: {next_bet}")
    
    # Verify if we Win this bet:
    payout = next_bet * odds
    profit = payout - next_bet
    net = profit - loss # Net result after recovering previous loss
    print(f"If Win: Profit={profit}, Net={net}")
    # Profit = 20.408 * 0.98 = 20.
    # Net = 20 - 10 = 10. Correct.
    
    assert abs(net - target) < 0.0001
    
    # Case 2: Zodiac (Odds 11). Target Profit 10.
    # Round 1: Bet 10. Loss.
    loss = 10
    odds = 11.0
    
    next_bet = (loss + target) / (odds - 1)
    # 20 / 10 = 2.0
    
    print(f"\nCase 2: Loss {loss}, Target {target}, Odds {odds}")
    print(f"Next Bet Needed: {next_bet}")
    
    payout = next_bet * odds
    profit = payout - next_bet
    net = profit - loss
    print(f"If Win: Profit={profit}, Net={net}")
    # Profit = 2 * 10 = 20.
    # Net = 20 - 10 = 10. Correct.
    
    assert abs(net - target) < 0.0001
    
    print("\nVerified!")

if __name__ == "__main__":
    test_loss_recovery()
