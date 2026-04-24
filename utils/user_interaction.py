from dataclasses import dataclass
from typing import Optional


@dataclass
class SessionSummary:
    session_id: Optional[str]
    status: Optional[str]
    total_games: int
    wins: int
    losses: int
    win_rate: float
    total_profit: float
    total_duration_seconds: float

    @staticmethod
    def from_dict(data):
        return SessionSummary(
            session_id=data.get("session_id"),
            status=data.get("status") or data.get("end_reason"),
            total_games=int(data.get("total_games", data.get("total_bets", 0))),
            wins=int(data.get("wins", 0)),
            losses=int(data.get("losses", 0)),
            win_rate=float(data.get("win_rate", 0.0)),
            total_profit=float(data.get("total_profit", data.get("profit", 0.0))),
            total_duration_seconds=float(data.get("total_duration_seconds", 0.0)),
        )


class GameStatusDisplay:
    def displayCurrentStatus(self, gambler_id, stake_status, game_status=None):
        print("\n--- Current Status ---")
        print(f"Gambler ID: {gambler_id}")
        print(f"Current Stake: {stake_status.get('current_stake', 'N/A')}")
        print(f"Boundary Status: {stake_status.get('boundary_status', stake_status.get('status', 'N/A'))}")
        if game_status:
            print(f"Session Status: {game_status.get('status', 'N/A')}")
            print(f"Games Played: {game_status.get('total_games', 0)}")

    def displayGameOutcome(self, result):
        bet = result.get("bet", {})
        settlement = result.get("settlement", {})
        print("\n--- Game Outcome ---")
        print(f"Bet ID: {bet.get('bet_id', 'N/A')}")
        print(f"Outcome: {'WIN' if bet.get('is_win') else 'LOSS'}")
        print(f"Stake Before: {bet.get('stake_before', settlement.get('balance_before', 'N/A'))}")
        print(f"Stake After: {bet.get('stake_after', settlement.get('balance_after', 'N/A'))}")
        print(f"Boundary Status: {settlement.get('boundary_status', 'N/A')}")

    def displaySessionSummary(self, summary):
        normalized = SessionSummary.from_dict(summary)
        print("\n--- Session Summary ---")
        print(f"Session ID: {normalized.session_id}")
        print(f"Status: {normalized.status}")
        print(f"Games: {normalized.total_games}")
        print(f"Wins/Losses: {normalized.wins}/{normalized.losses}")
        print(f"Win Rate: {normalized.win_rate:.2%}")
        print(f"Profit: {normalized.total_profit}")
        print(f"Duration (s): {normalized.total_duration_seconds}")


class InteractiveMenu:
    def __init__(self, input_handler):
        self.input_handler = input_handler

    def displayMainMenu(self):
        print("\n===== GAMBLER PROFILE MANAGEMENT =====")
        print("1. Create Gambler")
        print("2. Get Gambler Details")
        print("3. Update Gambler")
        print("4. Validate Gambler")
        print("5. Reset Gambler")
        print("6. Track Current Stake")
        print("7. Process Bet Outcome")
        print("8. Deposit Funds")
        print("9. Withdraw Funds")
        print("10. Stake Fluctuation Monitor")
        print("11. Validate Stake Boundaries")
        print("12. Stake History Report")
        print("13. Place Single Bet (Probability)")
        print("14. Place Consecutive Strategy Bets")
        print("15. Get Betting Session Summary")
        print("16. Start Game Session")
        print("17. Continue Game Session")
        print("18. Pause Game Session")
        print("19. Resume Game Session")
        print("20. End Game Session")
        print("21. Get Game Session")
        print("22. List Active Game Sessions")
        print("23. Win/Loss Analysis")
        print("24. Exit")
        print("25. Simple Game Demo")
        return input("Enter choice: ").strip()

    def promptForBetAmount(self, prompt="Enter bet amount: "):
        return self.input_handler.prompt_number(prompt, "bet_amount")


class SimpleGameEngine:
    def __init__(self, service, menu, display):
        self.service = service
        self.menu = menu
        self.display = display

    def run_demo(self):
        gid = self.menu.input_handler.prompt_number("Enter gambler ID: ", "gambler_id", cast_type=int)
        stake_status = self.service.get_stake_status(gid)
        self.display.displayCurrentStatus(gid, stake_status)

        amount = self.menu.promptForBetAmount()
        probability = self.menu.input_handler.prompt_number("Enter win probability (0-1): ", "probability")

        result = self.service.place_single_bet(gid, amount, probability)
        self.display.displayGameOutcome(result)

        updated = self.service.get_stake_status(gid)
        self.display.displayCurrentStatus(gid, updated)
