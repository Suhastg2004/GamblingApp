from config.init_db import create_database, create_tables
from services.gambler_profile_service import GamblerProfileService
from utils.safe_input_handler import SafeInputHandler
from utils.logger import logger

def initialize():
    try:
        print("Initializing database...")
        create_database()
        create_tables()
        print("Database ready.\n")
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"DB Initialization failed: {e}")
        print("Database setup failed. Check logs.")
        exit()

def run_app():
    service = GamblerProfileService()
    input_handler = SafeInputHandler()

    while True:
        try:
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

            ch = input("Enter choice: ").strip()

            if ch == "1":
                name = input("Enter name: ")
                initial_stake = input_handler.prompt_number("Enter initial stake: ", "initial_stake")
                win_th = input_handler.prompt_number("Enter win threshold: ", "win_threshold")
                loss_th = input_handler.prompt_number("Enter loss threshold: ", "loss_threshold")
                min_bet = input_handler.prompt_number("Enter min bet: ", "min_bet")
                max_bet = input_handler.prompt_number("Enter max bet: ", "max_bet")
                strategy = input("Enter strategy: ")
                session_limit = input_handler.prompt_number("Enter session limit: ", "session_limit", cast_type=int)

                gid = service.create_gambler(
                    name, initial_stake, win_th, loss_th,
                    min_bet, max_bet, strategy, session_limit
                )

                print(f"Gambler created with ID: {gid}")

            elif ch == "2":
                gid = int(input("Enter gambler ID: "))
                data = service.get_gambler(gid)

                if not data["profile"]:
                    print("Gambler not found")
                else:
                    print("\n--- Profile ---")
                    print(data["profile"])
                    print("\n--- Preferences ---")
                    print(data["preferences"])
                    print("\n--- Statistics ---")
                    print(data["statistics"])

            elif ch == "3":
                gid = int(input("Enter gambler ID: "))
                name = input("Enter new name (leave blank to skip): ").strip()
                win_th = input("Enter new win threshold (blank to skip): ").strip()
                loss_th = input("Enter new loss threshold (blank to skip): ").strip()

                name = name if name else None
                win_th = float(win_th) if win_th else None
                loss_th = float(loss_th) if loss_th else None

                service.update_gambler(gid, name, win_th, loss_th)
                print("Gambler updated successfully")

            elif ch == "4":
                gid = int(input("Enter gambler ID: "))
                valid = service.validate_gambler(gid)

                print("Eligible" if valid else "Not Eligible")

            elif ch == "5":
                gid = int(input("Enter gambler ID: "))
                service.reset_gambler(gid)
                print("Gambler reset successfully")

            elif ch == "6":
                gid = int(input("Enter gambler ID: "))
                status = service.get_stake_status(gid)
                print("\n--- Stake Status ---")
                print(status)

            elif ch == "7":
                gid = int(input("Enter gambler ID: "))
                amount = float(input("Enter bet amount: "))
                is_win_input = input("Did gambler win? (y/n): ").strip().lower()
                is_win = is_win_input == "y"
                payout_multiplier = float(input("Enter payout multiplier (default 2.0): ") or "2.0")
                bet_id = input("Enter bet id (optional): ").strip() or None
                result = service.process_bet(gid, amount, is_win, payout_multiplier, bet_id)
                print("\n--- Bet Result ---")
                print(result)

            elif ch == "8":
                gid = int(input("Enter gambler ID: "))
                amount = float(input("Enter deposit amount: "))
                note = input("Enter note (optional): ").strip() or None
                result = service.deposit(gid, amount, note)
                print("\n--- Deposit Result ---")
                print(result)

            elif ch == "9":
                gid = int(input("Enter gambler ID: "))
                amount = float(input("Enter withdrawal amount: "))
                note = input("Enter note (optional): ").strip() or None
                result = service.withdraw(gid, amount, note)
                print("\n--- Withdrawal Result ---")
                print(result)

            elif ch == "10":
                gid = int(input("Enter gambler ID: "))
                monitor = service.get_stake_monitor(gid)
                print("\n--- Stake Monitor ---")
                print(monitor)

            elif ch == "11":
                gid = int(input("Enter gambler ID: "))
                result = service.validate_stake_boundaries(gid)
                print("\n--- Boundary Validation ---")
                print(result)

            elif ch == "12":
                gid = int(input("Enter gambler ID: "))
                tx_type = input("Filter by transaction type (optional): ").strip() or None
                limit = int(input("Enter report row limit (default 200): ") or "200")
                report = service.get_stake_history_report(gid, tx_type, limit)
                print("\n--- Stake History Report ---")
                print(report)

            elif ch == "13":
                gid = input_handler.prompt_number("Enter gambler ID: ", "gambler_id", cast_type=int)
                amount = input_handler.prompt_number("Enter bet amount: ", "bet_amount")
                win_probability = input_handler.prompt_number("Enter win probability (0-1): ", "probability")
                odds_input = input("Enter odds multiplier (blank for auto): ").strip()
                odds_multiplier = (
                    input_handler.validator.parse_and_validate_numeric(odds_input, "odds_multiplier")
                    if odds_input
                    else None
                )
                outcome_strategy = input("Outcome strategy [RANDOM/WEIGHTED] (default RANDOM): ").strip() or "RANDOM"
                house_edge_input = input("House edge for WEIGHTED (default 0.0): ").strip()
                house_edge = (
                    input_handler.validator.parse_and_validate_numeric(house_edge_input, "house_edge")
                    if house_edge_input
                    else 0.0
                )
                odds_type = input("Odds type [FIXED/PROBABILITY_BASED/AMERICAN/DECIMAL] (blank for auto): ").strip() or None
                odds_value_input = input("Odds value for selected type (blank if not needed): ").strip()
                odds_value = (
                    input_handler.validator.parse_and_validate_numeric(odds_value_input, "odds_value")
                    if odds_value_input
                    else None
                )

                result = service.place_single_bet(
                    gid,
                    amount,
                    win_probability,
                    odds_multiplier,
                    outcome_strategy=outcome_strategy,
                    house_edge=house_edge,
                    odds_type=odds_type,
                    odds_value=odds_value,
                )
                print("\n--- Single Bet ---")
                print(result)

            elif ch == "14":
                gid = int(input("Enter gambler ID: "))
                strategy_name = input(
                    "Enter strategy [fixed, percentage, martingale, reverse_martingale, fibonacci, dalembert]: "
                ).strip()
                win_probability = float(input("Enter win probability (0-1): "))
                rounds = int(input("Enter number of consecutive bets: "))
                base_bet = float(input("Enter base bet amount: "))
                odds_input = input("Enter odds multiplier (blank for auto): ").strip()
                odds_multiplier = float(odds_input) if odds_input else None
                pct_input = input("Enter percentage for percentage strategy (default 0.05): ").strip()
                percentage = float(pct_input) if pct_input else 0.05
                step_input = input("Enter step for dalembert strategy (default 1.0): ").strip()
                step = float(step_input) if step_input else 1.0
                stop_input = input("Stop on boundary breach? (y/n, default y): ").strip().lower()
                stop_on_boundary = stop_input != "n"

                result = service.place_strategy_bets(
                    gid,
                    strategy_name,
                    win_probability,
                    rounds,
                    base_bet,
                    odds_multiplier=odds_multiplier,
                    percentage=percentage,
                    step=step,
                    stop_on_boundary=stop_on_boundary,
                )
                print("\n--- Consecutive Strategy Bets ---")
                print(result)

            elif ch == "15":
                session_id = input("Enter betting session ID: ").strip()
                summary = service.get_betting_session_summary(session_id)
                print("\n--- Betting Session Summary ---")
                print(summary)

            elif ch == "16":
                gid = int(input("Enter gambler ID: "))
                lower_limit = float(input("Enter lower stake limit: "))
                upper_limit = float(input("Enter upper stake limit: "))
                min_bet = float(input("Enter session min bet: "))
                max_bet = float(input("Enter session max bet: "))
                max_games = int(input("Enter max games in session: "))
                max_duration_seconds = int(input("Enter max duration in seconds: "))
                default_win_probability = float(input("Enter default win probability (0-1): "))

                session = service.start_game_session(
                    gid,
                    lower_limit,
                    upper_limit,
                    min_bet,
                    max_bet,
                    max_games,
                    max_duration_seconds,
                    default_win_probability,
                )
                print("\n--- Game Session Started ---")
                print(session)

            elif ch == "17":
                session_id = input("Enter game session ID: ").strip()
                rounds = int(input("Enter number of rounds to play: "))
                bet_amount_input = input("Enter fixed bet amount (blank for session min bet): ").strip()
                win_prob_input = input("Enter win probability (blank for session default): ").strip()
                odds_input = input("Enter odds multiplier (blank for auto): ").strip()

                bet_amount = float(bet_amount_input) if bet_amount_input else None
                win_probability = float(win_prob_input) if win_prob_input else None
                odds_multiplier = float(odds_input) if odds_input else None

                result = service.continue_game_session(
                    session_id,
                    rounds,
                    bet_amount=bet_amount,
                    win_probability=win_probability,
                    odds_multiplier=odds_multiplier,
                )
                print("\n--- Game Session Continued ---")
                print(result)

            elif ch == "18":
                session_id = input("Enter game session ID: ").strip()
                reason = input("Enter pause reason (optional): ").strip() or "User requested pause"
                result = service.pause_game_session(session_id, reason)
                print("\n--- Game Session Paused ---")
                print(result)

            elif ch == "19":
                session_id = input("Enter game session ID: ").strip()
                result = service.resume_game_session(session_id)
                print("\n--- Game Session Resumed ---")
                print(result)

            elif ch == "20":
                session_id = input("Enter game session ID: ").strip()
                reason = input(
                    "Enter end reason [MANUAL/TIMEOUT/UPPER_LIMIT_REACHED/LOWER_LIMIT_REACHED/MAX_GAMES_REACHED] (default MANUAL): "
                ).strip() or "MANUAL"
                result = service.end_game_session(session_id, reason)
                print("\n--- Game Session Ended ---")
                print(result)

            elif ch == "21":
                session_id = input("Enter game session ID: ").strip()
                result = service.get_game_session(session_id)
                print("\n--- Game Session Details ---")
                print(result)

            elif ch == "22":
                result = service.list_active_game_sessions()
                print("\n--- Active Game Sessions ---")
                print(result)

            elif ch == "23":
                gid = input_handler.prompt_number("Enter gambler ID: ", "gambler_id", cast_type=int)
                session_id = input("Enter betting session ID (optional): ").strip() or None
                limit = input_handler.prompt_number(
                    "Enter analysis bet limit (default 500): ",
                    "analysis_limit",
                    cast_type=int,
                    allow_blank=True,
                    default=500,
                )
                analysis = service.get_win_loss_analysis(gid, session_id=session_id, limit=limit)
                print("\n--- Win/Loss Analysis ---")
                print(analysis)

            elif ch == "24":
                print("Exiting application...")
                break

            else:
                print("Invalid choice")

        except ValueError as ve:
            logger.warning(f"Invalid input: {ve}")
            print(f"Invalid input: {ve}")

        except Exception as e:
            logger.error(f"Application error: {e}")
            print("Something went wrong. Check logs.")

if __name__ == "__main__":
    initialize()  # ensures DB + tables exist
    run_app()  # runs UC1 + UC2